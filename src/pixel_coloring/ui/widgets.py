from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

from ..rendering.progress_preview import ProgressPreview
from ..rendering.tile_cache import rgb_image
from .i18n import number, tr


def readable(text):
    # Use text labels rather than platform-dependent symbol-font glyphs.
    for symbol in ("▦", "⌂", "◷", "↗", "⚙", "✓", "↶", "↷", "→"):
        text = text.replace(symbol, "")
    return text.replace("＋", "+").strip()


def label(text, kind=None):
    widget = QLabel(readable(text))
    widget.setWordWrap(True)
    if kind:
        widget.setObjectName(kind)
    return widget


def button(text, callback, primary=False):
    widget = QPushButton(readable(text))
    if primary:
        widget.setObjectName("primary")
    widget.clicked.connect(callback)
    return widget


class ResponsiveGrid(QWidget):
    resized = Signal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


class GameActionButton(QPushButton):
    """Compact home/save actions matching the painting toolbar."""

    def __init__(self, action, callback):
        super().__init__()
        self.action = action
        self.setFixedSize(48, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(tr("Koleksiyona dön") if action == "home" else tr("Kaydet"))
        self.setToolTip(self.accessibleName() if action == "home" else tr("Kaydet · Ctrl+S"))
        self.clicked.connect(callback)

    def paintEvent(self, event):
        super().paintEvent(event)
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#A9DDCE") if self.underMouse() else QColor("#E6E6E6")
        q.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        q.setBrush(Qt.BrushStyle.NoBrush)
        if self.action == "home":
            q.drawPolyline(QPolygonF([QPointF(9, 21), QPointF(24, 8), QPointF(39, 21)]))
            q.drawPolyline(QPolygonF([QPointF(13, 19), QPointF(13, 35), QPointF(21, 35),
                                     QPointF(21, 25), QPointF(28, 25), QPointF(28, 35),
                                     QPointF(35, 35), QPointF(35, 19)]))
        else:
            q.drawPolygon(QPolygonF([QPointF(12, 9), QPointF(31, 9), QPointF(37, 15),
                                    QPointF(37, 35), QPointF(12, 35)]))
            q.drawRect(QRectF(17, 9, 12, 10))
            q.drawLine(25, 12, 25, 16)
            q.drawRoundedRect(QRectF(17, 25, 15, 10), 1, 1)
        q.end()


class FillButton(QPushButton):
    """One mode toggle: pencil for single cells, bucket for connected areas."""
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setFixedSize(48, 44)
        self.toggled.connect(self.update_mode)
        self.update_mode(False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def update_mode(self, enabled):
        self.setAccessibleName(tr("Toplu boya") if enabled else tr("Tekli boya"))
        self.setToolTip(tr("Toplu boya açık; tekli boyaya geç") if enabled else tr("Tekli boya açık; toplu boyaya geç"))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#17242A") if self.isChecked() else QColor("#E6E6E6")
        q.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        q.setBrush(Qt.BrushStyle.NoBrush)
        if self.isChecked():
            q.drawRoundedRect(QRectF(15, 17, 20, 21), 1, 1)
            q.drawRoundedRect(QRectF(10, 7, 30, 19), 6, 6)
            q.drawLine(15, 17, 35, 17)
            q.drawLine(22, 18, 22, 27)
            q.drawLine(27, 18, 27, 23)
        else:
            q.drawPolygon(QPolygonF([QPointF(11, 27), QPointF(30, 8), QPointF(39, 17),
                                     QPointF(20, 36), QPointF(11, 36)]))
            q.drawLine(11, 27, 20, 36)
            q.drawLine(26, 12, 35, 21)
            q.drawLine(16, 31, 31, 16)
        q.end()


class HintButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setFixedSize(48, 44)
        self.setAccessibleName(tr("Boyanmamış pikselleri göster"))
        self.setToolTip(tr("Boyanmamış pikselleri mini haritada kırmızı göster / gizle"))

    def paintEvent(self, event):
        super().paintEvent(event)
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        q.setPen(QPen(QColor("#FFE45E"), 2))
        q.setBrush(QColor("#FFE45E") if self.isChecked() else Qt.BrushStyle.NoBrush)
        q.drawEllipse(QRectF(16, 8, 16, 19))
        q.drawLine(20, 27, 28, 27)
        q.drawLine(20, 31, 28, 31)
        q.drawLine(22, 35, 26, 35)
        for x0, y0, x1, y1 in [(24, 2, 24, 5), (10, 9, 13, 11), (35, 11, 38, 9),
                               (9, 20, 12, 20), (36, 20, 39, 20)]:
            q.drawLine(x0, y0, x1, y1)
        q.end()


class Palette(QWidget):
    selected = Signal(int)
    columns = 5
    cell = 46

    def __init__(self, session):
        super().__init__()
        self.session = session
        self.setFixedSize(self.columns * self.cell, ((len(session.painting.palette) + 4) // 5) * self.cell)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        p = self.session.painting
        for i, rgb in enumerate(p.palette):
            x, y = i % self.columns * self.cell, i // self.columns * self.cell
            color = QColor(*[int(v) for v in rgb])
            painter.setBrush(color)
            painter.setPen(
                QPen(
                    QColor("#F6F1E9") if i == self.session.selected else QColor("#505965"),
                    3 if i == self.session.selected else 1,
                )
            )
            painter.drawRoundedRect(QRectF(x + 4, y + 4, 36, 36), 8, 8)
            painter.setPen(QColor("#161B23") if color.lightness() > 145 else QColor("#FFFFFF"))
            if p.counts[i] == p.totals[i]:
                painter.drawLine(x + 13, y + 22, x + 20, y + 29)
                painter.drawLine(x + 20, y + 29, x + 31, y + 15)
            else:
                painter.drawText(QRectF(x + 4, y + 4, 36, 36), Qt.AlignmentFlag.AlignCenter, str(i + 1))
        painter.end()

    def index_at(self, pos):
        return int(pos.y()) // self.cell * self.columns + int(pos.x()) // self.cell

    def mousePressEvent(self, event):
        i = self.index_at(event.position())
        if event.button() == Qt.MouseButton.LeftButton and i < len(self.session.painting.palette):
            self.selected.emit(i)

    def mouseMoveEvent(self, event):
        i = self.index_at(event.position())
        p = self.session.painting
        if i < len(p.palette):
            self.setToolTip(tr('Renk {number} · {remaining} hücre kaldı', number=i+1,
                               remaining=number(int(p.totals[i] - p.counts[i]))))


class Minimap(QWidget):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        painting = canvas.session.painting
        scale = min(230 / painting.width, 290 / painting.height)
        self.setFixedSize(max(1, round(painting.width * scale)), max(1, round(painting.height * scale)))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview = ProgressPreview(painting, self.width(), self.height())
        self.image = rgb_image(self.preview.rgb)
        self.show_remaining = False
        self.dirty = None
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setSingleShot(True)
        self.refresh_timer.setInterval(100)
        self.refresh_timer.timeout.connect(self.refresh_progress)
        self.setToolTip(
            tr("Gri: boyanmamış · Renkli: boyanmış · Çerçeve: baktığınız alan\nGitmek için tıklayın.")
        )
        self.rect_image = QRectF()
        canvas.camera_changed.connect(self.update)
        canvas.region_changed.connect(self.invalidate_progress)

    def set_remaining(self, enabled):
        self.show_remaining = enabled
        if self.dirty is not None:
            self.refresh_progress()
        else:
            self.update_image()

    def update_image(self):
        rgb = self.preview.rgb.copy()
        if self.show_remaining:
            import numpy as np

            marks = self.preview.remaining_cells()
            # Make a single remaining source pixel visible even in a huge picture.
            padded = np.pad(marks, 1)
            visible = marks.copy()
            for dy in range(3):
                for dx in range(3):
                    visible |= padded[dy:dy + marks.shape[0], dx:dx + marks.shape[1]]
            rgb[visible] = [255, 48, 80]
        self.image = rgb_image(rgb)
        self.update()

    def invalidate_progress(self, x0, y0, x1, y1):
        if self.dirty is not None:
            a, b, c, d = self.dirty
            x0, y0, x1, y1 = min(a, x0), min(b, y0), max(c, x1), max(d, y1)
        self.dirty = (x0, y0, x1, y1)
        if not self.refresh_timer.isActive():
            self.refresh_timer.start()

    def refresh_progress(self):
        if self.dirty is None:
            return
        self.preview.refresh(self.dirty)
        self.dirty = None
        self.update_image()

    def paintEvent(self, event):
        q = QPainter(self)
        q.fillRect(self.rect(), QColor("#1B2027"))
        p, c = self.canvas.session.painting, self.canvas.camera
        scale_x, scale_y = self.width() / p.width, self.height() / p.height
        self.rect_image = QRectF(0, 0, self.width(), self.height())
        q.drawImage(self.rect_image, self.image)
        q.setClipRect(self.rect_image)
        q.setPen(QPen(QColor("#F06C3B"), 2))
        left, top, width, height = c.view_bounds()
        visible = QRectF(
                self.rect_image.x() + (left - c.pan_x) / c.zoom * scale_x,
                self.rect_image.y() + (top - c.pan_y) / c.zoom * scale_y,
                width / c.zoom * scale_x,
                height / c.zoom * scale_y,
            ).intersected(self.rect_image)
        q.drawRect(visible.adjusted(1, 1, -1, -1))
        q.end()

    def mousePressEvent(self, event):
        if not self.rect_image.contains(event.position()):
            return
        p, c = self.canvas.session.painting, self.canvas.camera
        x = (event.position().x() - self.rect_image.x()) / self.rect_image.width() * p.width
        y = (event.position().y() - self.rect_image.y()) / self.rect_image.height() * p.height
        c.pan_x, c.pan_y = self.canvas.width() / 2 - x * c.zoom, self.canvas.height() / 2 - y * c.zoom
        self.canvas.constrain_camera()
        self.canvas.update()
        self.canvas.camera_changed.emit()
