"""Live, persistent canvas preferences, available from the game toolbar."""

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QMenu,
    QPushButton,
    QSpinBox,
    QWidget,
    QWidgetAction,
)

from .i18n import tr

DEFAULTS = {'numbers': True, 'grid': True, 'number_scale': 100,
            'grid_width': 1, 'grid_opacity': .22, 'completion_animation': True}


class AppearanceMenu(QMenu):
    changed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.controls = {}
        panel = QWidget()
        form = QFormLayout(panel)
        form.setContentsMargins(18, 14, 18, 14)
        for key, caption in [('numbers', 'Hücre numaraları'), ('grid', 'Hücre ızgarası'),
                             ('completion_animation', 'Tamamlanma animasyonu')]:
            control = QCheckBox(tr(caption))
            control.toggled.connect(lambda value, key=key: self.set_value(key, value))
            self.controls[key] = control
            form.addRow(control)
        for key, caption, low, high, suffix in [
            ('number_scale', 'Numara boyutu', 50, 200, '%'),
            ('grid_width', 'Izgara kalınlığı', 1, 4, ' px'),
            ('grid_opacity', 'Izgara yoğunluğu', 0, 100, '%'),
        ]:
            control = QSpinBox()
            control.setRange(low, high)
            control.setSuffix(suffix)
            control.setAccessibleName(tr(caption))
            control.valueChanged.connect(lambda value, key=key: self.set_value(
                key, value / 100 if key == 'grid_opacity' else value))
            self.controls[key] = control
            form.addRow(tr(caption), control)
        reset = QPushButton(tr('Varsayılan görünüm'))
        reset.clicked.connect(self.reset)
        form.addRow(reset)
        action = QWidgetAction(self)
        action.setDefaultWidget(panel)
        self.addAction(action)
        self.aboutToShow.connect(self.sync)
        self.sync()

    def sync(self):
        for key, control in self.controls.items():
            value = self.settings.get(key, DEFAULTS[key])
            with QSignalBlocker(control):
                if isinstance(control, QCheckBox):
                    control.setChecked(value)
                else:
                    control.setValue(round(value * 100) if key == 'grid_opacity' else value)

    def set_value(self, key, value):
        self.settings[key] = value
        self.changed.emit()

    def reset(self):
        self.settings.update(DEFAULTS)
        self.sync()
        self.changed.emit()
