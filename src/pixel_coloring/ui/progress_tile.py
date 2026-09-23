from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QPushButton


class ProgressTile(QPushButton):
    """A perimeter meter and readable badge for saved painting progress."""
    def __init__(self, percent):
        super().__init__()
        self.percent = max(0, min(100, percent))

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.percent <= 0:
            return
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor('#8AE1B3' if self.percent >= 100 else '#FFB779')
        q.setPen(QPen(color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        x, y, w, h = 3, 3, self.width()-6, self.height()-6
        remaining = 2*(w+h)*self.percent/100
        for sx, sy, dx, dy, length in [(x,y,1,0,w), (x+w,y,0,1,h),
                                       (x+w,y+h,-1,0,w), (x,y+h,0,-1,h)]:
            amount = min(length, remaining)
            if amount > 0:
                q.drawLine(QPointF(sx,sy), QPointF(sx+dx*amount,sy+dy*amount))
            remaining -= amount
        badge = QRectF(19, self.height()-25, self.width()-38, 21)
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor('#172B27'))
        q.drawRoundedRect(badge, 5, 5)
        q.setPen(color)
        q.setFont(QFont('Noto Sans', 9, QFont.Weight.Bold))
        text = 'Bitti' if self.percent >= 100 else f'%{self.percent:.1f}'.replace('.', ',')
        q.drawText(badge, Qt.AlignmentFlag.AlignCenter, text)
        q.end()
