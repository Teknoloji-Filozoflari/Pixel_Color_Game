from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QMenu

from ..core.timelapse import Timelapse
from .i18n import tr


class RecordingMenu(QMenu):
    export_requested = Signal()

    def __init__(self, canvas, button):
        super().__init__(button)
        self.button = button
        self.recorder = Timelapse(canvas.session.painting)
        self.toggle_action = self.addAction(tr('Kaydı başlat / sürdür'), self.toggle)
        self.export_action = self.addAction(tr('GIF olarak kaydet'), self.export_requested.emit)
        self.addSeparator()
        note = self.addAction(tr('Kayıt bu resim açıkken tutulur. Çıkmadan GIF kaydet.'))
        note.setEnabled(False)
        canvas.changed.connect(self.recorder.changed)
        self.timer = QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.recorder.capture)
        self.aboutToShow.connect(self.sync)
        self.sync()

    def toggle(self):
        if self.recorder.active:
            self.pause()
        else:
            self.recorder.start()
            self.timer.start()
        self.sync()

    def pause(self):
        self.timer.stop()
        self.recorder.pause()
        self.sync()

    def sync(self):
        self.toggle_action.setText(tr('Kaydı duraklat') if self.recorder.active else tr('Kaydı başlat / sürdür'))
        self.export_action.setEnabled(bool(self.recorder.frames))
        self.button.setChecked(self.recorder.active)
