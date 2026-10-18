"""Adjust and preview a raster import without writing files or player progress."""

from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image
from PySide6.QtCore import QRect, QSignalBlocker, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..importer.image_importer import automatic_color_count, convert_image, load_image
from ..rendering.tile_cache import rgb_image
from .i18n import number, tr, translate_error


class ImagePreview(QWidget):
    def __init__(self, smooth=False):
        super().__init__()
        self.pixmap = QPixmap()
        self.smooth = smooth
        self.setMinimumSize(180, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_rgb(self, rgb):
        self.pixmap = QPixmap.fromImage(rgb_image(rgb))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#1B2027'))
        if not self.pixmap.isNull():
            size = self.pixmap.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            target = QRect((self.width() - size.width()) // 2, (self.height() - size.height()) // 2,
                           size.width(), size.height())
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self.smooth)
            painter.drawPixmap(target, self.pixmap)
        painter.end()


def build_preview(path, size, colors):
    source = load_image(path)
    painting = convert_image(source, path.stem, colors, size)
    source.thumbnail((480, 360), Image.Resampling.LANCZOS)
    # Bound the display raster too; the full target map remains in painting.
    converted = Image.fromarray(painting.palette[painting.target_map])
    converted.thumbnail((480, 360), Image.Resampling.NEAREST)
    return painting, np.asarray(source).copy(), np.asarray(converted).copy()


class ImportPreviewDialog(QDialog):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        with Image.open(path) as image:
            width, height = image.size
            if image.getexif().get(274) in (5, 6, 7, 8):
                width, height = height, width
        self.original_size = width, height
        self.painting = None
        self.revision = 0
        self.applied_revision = -1
        self.job = None
        self.job_revision = -1
        self.closed = False
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='import-preview')
        self.setWindowTitle(tr('Resmini hazırla'))
        self.setMinimumSize(720, 520)
        self.resize(860, 620)
        root = QVBoxLayout(self)
        heading = QLabel(tr('Renk ve piksel ayarlarını önizle'))
        heading.setObjectName('subheading')
        root.addWidget(heading)
        root.addWidget(QLabel(tr('Özgün boyut: {width} × {height}', width=number(width), height=number(height))))
        controls = QGridLayout()
        self.width_box, self.height_box, self.colors_box = QSpinBox(), QSpinBox(), QSpinBox()
        self.width_box.setRange(1, 1920)
        self.height_box.setRange(1, 1080)
        self.colors_box.setRange(2, 256)
        self.width_box.setAccessibleName(tr('Genişlik'))
        self.height_box.setAccessibleName(tr('Yükseklik'))
        self.colors_box.setAccessibleName(tr('Renk sayısı'))
        factor = min(1, 1920 / width, 1080 / height)
        self.width_box.setValue(max(1, round(width * factor)))
        self.height_box.setValue(max(1, round(height * factor)))
        self.aspect_box = QCheckBox(tr('En boy oranını koru'))
        self.aspect_box.setChecked(True)
        self.auto_colors_box = QCheckBox(tr('Renk sayısını otomatik seç'))
        self.auto_colors_box.setChecked(True)
        for col, (caption, widget) in enumerate([
            (tr('Genişlik'), self.width_box), (tr('Yükseklik'), self.height_box),
            (tr('Renk sayısı'), self.colors_box),
        ]):
            controls.addWidget(QLabel(caption), 0, col)
            controls.addWidget(widget, 1, col)
        controls.addWidget(self.aspect_box, 2, 0, 1, 2)
        controls.addWidget(self.auto_colors_box, 2, 2)
        root.addLayout(controls)
        previews = QHBoxLayout()
        self.original_preview, self.converted_preview = ImagePreview(True), ImagePreview()
        for caption, preview in [(tr('Özgün resim'), self.original_preview),
                                 (tr('Boyama önizlemesi'), self.converted_preview)]:
            column = QVBoxLayout()
            column.addWidget(QLabel(caption))
            column.addWidget(preview, 1)
            previews.addLayout(column, 1)
        root.addLayout(previews, 1)
        self.status = QLabel()
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr('Koleksiyona ekle'))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr('İptal'))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)
        self.debounce = QTimer(self)
        self.debounce.setSingleShot(True)
        self.debounce.setInterval(160)
        self.debounce.timeout.connect(self.start_preview)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(40)
        self.poll_timer.timeout.connect(self.poll_preview)
        self.width_box.valueChanged.connect(lambda: self.dimensions_changed('width'))
        self.height_box.valueChanged.connect(lambda: self.dimensions_changed('height'))
        self.aspect_box.toggled.connect(lambda: self.dimensions_changed('width'))
        self.auto_colors_box.toggled.connect(self.schedule_preview)
        self.colors_box.valueChanged.connect(self.schedule_preview)
        self.schedule_preview()

    def dimensions_changed(self, axis):
        if self.aspect_box.isChecked():
            width, height = self.original_size
            factor = (min(self.width_box.value() / width, 1080 / height) if axis == 'width'
                      else min(self.height_box.value() / height, 1920 / width))
            with QSignalBlocker(self.width_box), QSignalBlocker(self.height_box):
                self.width_box.setValue(max(1, round(width * factor)))
                self.height_box.setValue(max(1, round(height * factor)))
        self.schedule_preview()

    def schedule_preview(self):
        if self.closed:
            return
        self.revision += 1
        self.painting = None
        self.colors_box.setEnabled(not self.auto_colors_box.isChecked())
        if self.auto_colors_box.isChecked():
            with QSignalBlocker(self.colors_box):
                self.colors_box.setValue(automatic_color_count(self.width_box.value(), self.height_box.value()))
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.status.setText(tr('Önizleme hazırlanıyor…'))
        self.debounce.start()

    def start_preview(self):
        if self.closed or self.job is not None:
            return
        self.job_revision = self.revision
        self.job = self.executor.submit(build_preview, self.path,
                                        (self.width_box.value(), self.height_box.value()), self.colors_box.value())
        self.poll_timer.start()

    def poll_preview(self):
        if self.closed or self.job is None or not self.job.done():
            return
        job, revision = self.job, self.job_revision
        self.job = None
        self.poll_timer.stop()
        try:
            painting, original, converted = job.result()
        except Exception as exc:
            if revision == self.revision:
                self.status.setText(tr('Önizleme hazırlanamadı: {error}', error=translate_error(exc)))
        else:
            if revision == self.revision:
                self.painting = painting
                self.applied_revision = revision
                self.original_preview.set_rgb(original)
                self.converted_preview.set_rgb(converted)
                self.status.setText(tr('Önizleme: {width} × {height} · {colors} renk · {cells} hücre',
                                       width=number(painting.width), height=number(painting.height),
                                       colors=number(len(painting.palette)), cells=number(painting.target_map.size)))
                self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
        if revision != self.revision:
            self.debounce.stop()
            self.start_preview()

    def accept(self):
        if self.painting is not None and self.applied_revision == self.revision:
            super().accept()

    def done(self, result):
        if self.closed:
            return
        self.closed = True
        self.debounce.stop()
        self.poll_timer.stop()
        self.executor.shutdown(wait=False, cancel_futures=True)
        super().done(result)
