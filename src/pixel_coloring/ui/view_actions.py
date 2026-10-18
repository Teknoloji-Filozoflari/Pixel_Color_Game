from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QPushButton

HIGHLIGHTS = {"Yeşil": (0, 255, 0), "Mavi": (0, 115, 255),
              "Mor": (210, 0, 255), "Turkuaz": (0, 255, 220)}


class ViewButton(QPushButton):
    def __init__(self, kind, tooltip):
        super().__init__()
        self.kind = kind
        self.tint = QColor('#E6E6E6')
        self.setFixedSize(42, 40)
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        super().paintEvent(event)
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor('#17242A') if self.isChecked() else self.tint
        q.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        q.setBrush(Qt.BrushStyle.NoBrush)
        if self.kind == 'grid':
            for p in (15, 27):
                q.drawLine(p, 9, p, 31)
                q.drawLine(10, p-1, 32, p-1)
        elif self.kind == 'appearance':
            for y, x in ((12, 18), (20, 27), (28, 15)):
                q.drawLine(10, y, 32, y)
                q.setBrush(self.palette().button())
                q.drawEllipse(QRectF(x - 3, y - 3, 6, 6))
                q.setBrush(Qt.BrushStyle.NoBrush)
        elif self.kind == 'info':
            q.drawEllipse(QRectF(11, 10, 20, 20))
            q.drawPoint(21, 15)
            q.drawLine(21, 19, 21, 26)
        elif self.kind == 'recording':
            q.drawRoundedRect(QRectF(10, 11, 22, 18), 3, 3)
            q.drawEllipse(QRectF(17, 16, 8, 8))
        elif self.kind == 'highlight':
            q.drawRect(QRectF(11, 10, 20, 20))
            for offset in (0, 6, 12):
                q.drawLine(12+offset, 29, 30, 11+offset)
                q.drawLine(12, 23-offset, 24-offset, 11)
        else:
            for x, dx in ((11, 6), (31, -6)):
                for y, dy in ((10, 6), (30, -6)):
                    q.drawLine(x, y, x+dx, y)
                    q.drawLine(x, y, x, y+dy)
        q.end()
