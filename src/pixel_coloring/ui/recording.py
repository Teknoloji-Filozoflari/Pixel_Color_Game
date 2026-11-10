from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QMenu

from ..core.timelapse import Timelapse
from .i18n import number, tr


class RecordingMenu(QMenu):
    export_requested = Signal()

    def __init__(self, canvas, button):
        super().__init__(button)
        self.button = button
        self.recorder = Timelapse(canvas.session.painting)
        self.start_action = self.addAction(tr('Kaydı başlat'), self.start)
        self.pause_action = self.addAction(tr('Kaydı duraklat'), self.pause)
        self.resume_action = self.addAction(tr('Kaydı sürdür'), self.resume)
        self.export_action = self.addAction(tr('GIF olarak kaydet'), self.export_requested.emit)
        self.addSeparator()
        self.status_action = self.addAction('')
        self.status_action.setEnabled(False)
        self.addSeparator()
        note = self.addAction(tr('Duraklatıp sonra sürebilirsin. Resimden çıkmadan GIF kaydet.'))
        note.setEnabled(False)
        canvas.changed.connect(self.recorder.changed)
        self.timer = QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.recorder.capture)
        self.aboutToShow.connect(self.sync)
        self.sync()

    def start(self):
        if self.recorder.frames and not self.recorder.active:
            self.resume()
            return
        self.recorder.start()
        self.timer.start()
        self.sync()

    def resume(self):
        if self.recorder.active:
            return
        self.recorder.start()
        self.timer.start()
        self.sync()

    def pause(self):
        self.timer.stop()
        self.recorder.pause()
        self.sync()

    def sync(self):
        has_frames = bool(self.recorder.frames)
        active = self.recorder.active
        self.start_action.setEnabled(not active and not has_frames)
        self.pause_action.setEnabled(active)
        self.resume_action.setEnabled(not active and has_frames)
        self.export_action.setEnabled(has_frames)
        if active:
            status = tr('Kayıt sürüyor · {count} kare', count=number(len(self.recorder.frames)))
        elif has_frames:
            status = tr('Duraklatıldı · {count} kare hazır', count=number(len(self.recorder.frames)))
        else:
            status = tr('Kayıt kapalı')
        self.status_action.setText(status)
        self.button.setChecked(active)
        if active:
            self.button.setToolTip(tr('Boyama kaydı · kayıt sürüyor'))
        elif has_frames:
            self.button.setToolTip(tr('Boyama kaydı · duraklatıldı, sürebilirsin'))
        else:
            self.button.setToolTip(tr('Boyama kaydı · GIF'))
