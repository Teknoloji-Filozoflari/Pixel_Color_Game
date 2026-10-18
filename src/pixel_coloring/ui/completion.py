"""A readable completion celebration over the finished artwork."""

import math
import random
import time

from PySide6.QtCore import QEvent, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)
from PySide6.QtWidgets import QBoxLayout, QPushButton, QWidget

from ..rendering.tile_cache import rgb_image
from .i18n import painting_title, tr


class CompletionOverlay(QWidget):
    finished = Signal()
    collection_requested = Signal()
    duration_ms = 3600
    COLORS = ('#F9D77B', '#A5F0CB', '#85D9FF', '#C5ADFF', '#FFBD85', '#F5FCFF')

    def __init__(self, canvas, animate=True):
        super().__init__(canvas)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAccessibleName(tr('Tamamlandı!'))
        painting = canvas.session.painting
        self.title = painting_title(painting.id, painting.title)
        self.artwork = QPixmap.fromImage(rgb_image(painting.palette[painting.target_map]))
        self.smooth_artwork = max(painting.width, painting.height) > 512
        # Stable trajectories; rendering never changes the global random state.
        rng = random.Random(24)
        self.confetti = [
            (i % 2, rng.uniform(0, .65), rng.uniform(.24, .82), rng.uniform(.8, 1.3),
             rng.uniform(5, 11), rng.uniform(0, 360), rng.uniform(-240, 240), i % 6, i % 3)
            for i in range(160)
        ]
        self.started = time.monotonic()
        self.ended = False
        self.awaiting_choice = False
        self.actions = QWidget(self)
        self.actions.setStyleSheet('background: transparent;')
        self.action_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.actions)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(10)
        self.collection_button = QPushButton(tr('Koleksiyona dön'))
        self.collection_button.setObjectName('completionCollection')
        self.collection_button.setStyleSheet(
            'QPushButton {background:#EBC96F; color:#1C302A; border:1px solid #F8DF9A; '
            'font-weight:600; padding:9px 12px;} '
            'QPushButton:hover {background:#FFE2A0;}')
        self.stay_button = QPushButton(tr('Resimde kal'))
        self.stay_button.setObjectName('completionStay')
        self.collection_button.clicked.connect(self.collection_requested.emit)
        self.stay_button.clicked.connect(self.stay)
        self.action_layout.addWidget(self.collection_button)
        self.action_layout.addWidget(self.stay_button)
        self.actions.hide()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.setGeometry(canvas.rect())
        canvas.installEventFilter(self)
        self.show()
        self.raise_()
        if animate:
            self.timer.start(16)
        else:
            self.finish_animation()

    def cancel(self):
        """Navigation stops the celebration without announcing completion later."""
        self.ended = True
        self.timer.stop()
        self.parentWidget().removeEventFilter(self)
        self.hide()
        self.deleteLater()

    def stay(self):
        self.cancel()
        self.parentWidget().setFocus()

    def finish_animation(self):
        if self.ended or self.awaiting_choice:
            return
        self.awaiting_choice = True
        self.timer.stop()
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.position_actions()
        self.actions.show()
        self.stay_button.setFocus()
        self.update()
        self.finished.emit()

    def eventFilter(self, watched, event):
        if watched is self.parentWidget() and event.type() == QEvent.Type.Resize:
            self.setGeometry(watched.rect())
        return super().eventFilter(watched, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'action_layout'):
            self.position_actions()

    def position_actions(self):
        scale = min(1, self.width() / 500, self.height() / 380)
        width = round(380 * scale)
        # Focus adds a thicker border in the app theme; reserve that space too.
        required = self.collection_button.sizeHint().width() + self.stay_button.sizeHint().width() + 18
        self.stacked_actions = required > width
        self.action_layout.setDirection(QBoxLayout.Direction.TopToBottom if self.stacked_actions
                                        else QBoxLayout.Direction.LeftToRight)
        height = 92 if self.stacked_actions else 44
        self.actions.resize(width, height)
        scale, center_y, _ = self.badge_geometry()
        self.actions.move(round((self.width() - width) / 2), round(center_y + 98 * scale))

    def badge_geometry(self):
        scale = min(1, self.width() / 500, self.height() / 380)
        bottom = 98 + (self.actions.height() + 18) / scale if self.awaiting_choice else 104
        center_y = max(16 + 104 * scale, min(self.height() * .61, self.height() - 16 - bottom * scale))
        return scale, center_y, bottom

    def tick(self):
        if self.ended or self.awaiting_choice:
            return
        if time.monotonic() - self.started >= self.duration_ms / 1000:
            self.finish_animation()
        else:
            self.setGeometry(self.parentWidget().rect())
            self.update()

    def paintEvent(self, event):
        elapsed = max(0, time.monotonic() - self.started)
        opacity = 1 if self.awaiting_choice else min(1, elapsed / .18)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, self.smooth_artwork)
        painter.setOpacity(opacity)
        painter.fillRect(self.rect(), QColor('#161F28'))
        # Reveal the whole finished picture even when the player finished zoomed in.
        size = self.artwork.size().scaled(self.size() * .94, Qt.AspectRatioMode.KeepAspectRatio)
        target = QRectF((self.width() - size.width()) / 2, (self.height() - size.height()) / 2,
                        size.width(), size.height())
        painter.drawPixmap(target, self.artwork, QRectF(self.artwork.rect()))
        shade = QLinearGradient(0, 0, 0, self.height())
        shade.setColorAt(0, QColor(9, 18, 28, 25))
        shade.setColorAt(1, QColor(9, 18, 28, 140))
        painter.fillRect(self.rect(), shade)
        if not self.awaiting_choice:
            self.draw_confetti(painter, elapsed)
        self.draw_badge(painter, elapsed)
        painter.end()

    def draw_confetti(self, painter, elapsed):
        scale = max(.7, min(1.4, self.width() / 800))
        painter.setPen(Qt.PenStyle.NoPen)
        for side, delay, vx, vy, size, phase, spin, color, shape in self.confetti:
            age = elapsed - delay
            if age < 0:
                continue
            direction = 1 if side == 0 else -1
            x = self.width() * ((.06 if side == 0 else .94) + direction * vx * age)
            y = self.height() * (.95 - vy * age + .38 * age * age)
            if not (-30 < x < self.width() + 30 and -30 < y < self.height() + 30):
                continue
            painter.save()
            painter.translate(x, y)
            painter.rotate(phase + spin * age)
            painter.setBrush(QColor(self.COLORS[color]))
            radius = size * scale
            if shape == 0:
                painter.drawEllipse(QRectF(-radius / 2, -radius / 2, radius, radius))
            else:
                flutter = .45 + .55 * abs(math.cos(age * 7 + phase))
                painter.drawRoundedRect(QRectF(-radius / 2, -radius * flutter / 2,
                                              radius, radius * flutter), 1, 1)
            painter.restore()

    def draw_badge(self, painter, elapsed):
        scale, center_y, bottom = self.badge_geometry()
        entrance = 1 if self.awaiting_choice else 1 - (1 - min(1, elapsed / .55)) ** 3
        painter.save()
        painter.translate(self.width() / 2, center_y + 25 * (1 - entrance))
        painter.scale(scale * (.9 + .1 * entrance), scale * (.9 + .1 * entrance))
        card = QRectF(-210, -104, 420, 104 + bottom)
        painter.setPen(Qt.PenStyle.NoPen)
        for expansion, alpha in ((16, 12), (10, 20), (4, 35)):
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRoundedRect(card.adjusted(-expansion, -expansion, expansion, expansion), 27, 27)
        background = QLinearGradient(card.topLeft(), card.bottomRight())
        background.setColorAt(0, QColor(26, 44, 50, 244))
        background.setColorAt(1, QColor(17, 29, 40, 249))
        painter.setBrush(background)
        painter.setPen(QPen(QColor('#70877F'), 1))
        painter.drawRoundedRect(card, 22, 22)
        glow = QRadialGradient(QPointF(0, -54), 57)
        glow.setColorAt(0, QColor(249, 215, 123, 100))
        glow.setColorAt(1, QColor(249, 215, 123, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(0, -54), 57, 57)
        medal = QLinearGradient(-25, -80, 25, -25)
        medal.setColorAt(0, QColor('#FFF1B5'))
        medal.setColorAt(1, QColor('#E7B95A'))
        painter.setBrush(medal)
        painter.drawEllipse(QPointF(0, -54), 29, 29)
        painter.setPen(QPen(QColor('#24483C'), 4, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawPolyline(QPolygonF([QPointF(-12, -54), QPointF(-3, -45), QPointF(13, -63)]))
        font = QFont('Noto Sans')
        font.setPixelSize(30)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor('#FFF3CB'))
        painter.drawText(QRectF(-195, -14, 390, 44), Qt.AlignmentFlag.AlignCenter, tr('Tamamlandı!'))
        font.setPixelSize(15)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor('#B9EBD6'))
        painter.drawText(QRectF(-195, 33, 390, 26), Qt.AlignmentFlag.AlignCenter,
                         tr('Her kareye renk kattın.'))
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QColor('#B0BFCA'))
        title = painter.fontMetrics().elidedText(self.title, Qt.TextElideMode.ElideRight, 360)
        painter.drawText(QRectF(-180, 65, 360, 24), Qt.AlignmentFlag.AlignCenter, title)
        painter.restore()
