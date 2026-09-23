from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QPushButton


class HomeAction(QPushButton):
    def __init__(self, kind, caption, callback):
        super().__init__()
        self.kind = kind
        self.setFixedSize(48, 44)
        self.setToolTip(caption)
        self.setAccessibleName(caption)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(callback)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = '#F3946F' if self.kind == 'exit' and self.underMouse() else '#D4E8E2'
        painter.setPen(QPen(QColor(color), 2, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.kind == 'add':
            painter.drawRoundedRect(QRectF(10, 10, 25, 23), 2, 2)
            painter.drawEllipse(QRectF(15, 14, 4, 4))
            painter.drawPolyline(QPolygonF([QPointF(11, 28), QPointF(20, 20),
                                           QPointF(25, 25), QPointF(29, 21)]))
            painter.fillRect(QRectF(29, 24, 13, 13), self.palette().button())
            painter.drawLine(35, 25, 35, 35)
            painter.drawLine(30, 30, 40, 30)
        elif self.kind == 'collection':
            for x in (11, 26):
                for y in (9, 24):
                    painter.drawRoundedRect(QRectF(x, y, 11, 11), 2, 2)
        elif self.kind == 'settings':
            painter.translate(24, 22)
            painter.drawEllipse(QRectF(-9, -9, 18, 18))
            painter.drawEllipse(QRectF(-3, -3, 6, 6))
            for _ in range(8):
                painter.drawLine(0, -9, 0, -13)
                painter.rotate(45)
        else:
            painter.drawLine(16, 14, 32, 30)
            painter.drawLine(32, 14, 16, 30)
        painter.end()
