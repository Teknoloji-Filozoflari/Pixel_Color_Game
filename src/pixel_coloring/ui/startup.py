"""Lightweight loading window: safe to import before NumPy and game modules."""
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter, QPixmap, QFont, QFontDatabase
from PySide6.QtWidgets import QWidget


class StartupScreen(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(560, 330)
        self.setWindowTitle('Piksel Atölyesi — Yükleniyor')
        QFontDatabase.addApplicationFont(str(Path(__file__).resolve().parents[1] / 'resources/fonts/NotoSans.ttf'))
        self.logo = QPixmap(str(Path(__file__).resolve().parents[1] / 'resources/icons/piksel-atolyesi.png'))
        self.message = 'Renkler hazırlanıyor…'
        self.value = 0
        self.frame = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(90)
        screen = self.screen().availableGeometry()
        self.move(screen.center() - self.rect().center())

    def animate(self):
        self.frame += 1
        self.update()

    def set_progress(self, value, message):
        self.value = max(self.value, min(100, value))
        self.message = message
        self.setAccessibleName(f'{message} %{int(self.value)}')
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor('#39464D'))
        p.setBrush(QColor('#20282E'))
        p.drawRoundedRect(QRectF(1, 1, 558, 328), 22, 22)
        p.drawPixmap(42, 42, 76, 76, self.logo)
        p.setPen(QColor('#F0784F'))
        p.setFont(QFont('Noto Sans', 23, QFont.Weight.Bold))
        p.drawText(QRectF(140, 43, 400, 42), 'PİKSEL ATÖLYESİ')
        p.setFont(QFont('Noto Sans', 11))
        p.setPen(QColor('#B7C8CE'))
        p.drawText(QRectF(142, 90, 380, 25), 'Bir resim, binlerce renkli an.')
        colors = ['#F0784F', '#EFC76C', '#85C7AD', '#62BECB', '#A498D5']
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(18):
            color = QColor(colors[i % len(colors)])
            color.setAlpha(255 if (i + self.frame) % 18 < 7 else 65)
            p.setBrush(color)
            p.drawRoundedRect(QRectF(43 + i * 27, 157, 19, 19), 3, 3)
        p.setPen(QColor('#E3ECEB'))
        p.drawText(QRectF(43, 213, 420, 25), self.message)
        p.setPen(QColor('#85C7AD'))
        p.drawText(QRectF(467, 213, 50, 25), Qt.AlignmentFlag.AlignRight, f'%{int(self.value)}')
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor('#35434A'))
        p.drawRoundedRect(QRectF(43, 254, 474, 7), 3, 3)
        if self.value:
            p.setBrush(QColor('#85C7AD'))
            p.drawRoundedRect(QRectF(43, 254, 474 * self.value / 100, 7), 3, 3)
        p.setPen(QColor('#90A4AC'))
        p.setFont(QFont('Noto Sans', 9))
        p.drawText(QRectF(43, 282, 474, 20), 'Atölyen açılıyor…')
        p.end()
