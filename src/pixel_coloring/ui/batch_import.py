from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QListWidget,
    QSpinBox,
    QVBoxLayout,
)

from .i18n import tr
from .widgets import label


class BatchImportDialog(QDialog):
    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('Toplu resim ekle'))
        self.resize(540, 480)
        layout = QVBoxLayout(self)
        layout.addWidget(label(tr('{count} dosya için ortak ayarlar', count=len(paths)), 'subheading'))
        files = QListWidget()
        files.addItems([path.name for path in paths])
        layout.addWidget(files)
        note = label(tr('Resimler orantılı küçültülür, büyütülmez. .pcolor dosyalarının hazır boyutu ve paleti korunur.'), 'muted')
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        self.width_spin, self.height_spin, self.colors_spin = QSpinBox(), QSpinBox(), QSpinBox()
        for control, caption, maximum, value in [
            (self.width_spin, 'En fazla genişlik', 1920, 640),
            (self.height_spin, 'En fazla yükseklik', 1080, 480),
            (self.colors_spin, 'Renk sayısı', 256, 32),
        ]:
            control.setRange(2 if control is self.colors_spin else 1, maximum)
            control.setValue(value)
            control.setAccessibleName(tr(caption))
            form.addRow(tr(caption), control)
        self.automatic = QCheckBox(tr('Renk sayısını otomatik seç'))
        self.automatic.setChecked(True)
        self.colors_spin.setEnabled(False)
        self.automatic.toggled.connect(lambda value: self.colors_spin.setEnabled(not value))
        form.addRow(self.automatic)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def options(self):
        return ((self.width_spin.value(), self.height_spin.value()),
                None if self.automatic.isChecked() else self.colors_spin.value())
