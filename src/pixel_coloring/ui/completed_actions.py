from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QPushButton

from .i18n import tr


class CompletedAction(QPushButton):
    """Camera for preview, play triangle for a new attempt."""

    def __init__(self, preview, callback):
        super().__init__()
        self.preview = preview
        self.setFixedSize(64, 44)
        self.setAccessibleName(tr("Önizle") if preview else tr("Baştan başla"))
        self.setToolTip(self.accessibleName())
        self.clicked.connect(callback)

    def paintEvent(self, event):
        super().paintEvent(event)
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor("#DDE4E7"))
        if self.preview:
            q.drawRoundedRect(QRectF(16, 14, 32, 22), 2, 2)
            q.drawRect(QRectF(23, 10, 12, 5))
            q.setBrush(QColor("#303841"))
            q.drawEllipse(QRectF(26, 18, 12, 12))
            q.setPen(QPen(QColor("#DDE4E7"), 2))
            q.drawEllipse(QRectF(28, 20, 8, 8))
        else:
            q.drawPolygon(QPolygonF([QPointF(25, 11), QPointF(44, 22), QPointF(25, 33)]))
        q.end()
