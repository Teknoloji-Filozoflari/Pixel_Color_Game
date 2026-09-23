from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPen, QPixmap, QPolygonF


def painting_pointer():
    """Compact outlined arrow; the physical tip is the painting hotspot."""
    pixmap = QPixmap(26, 34)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#17242A"), 1.5, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(QColor("#F4FFF9"))
    painter.drawPolygon(QPolygonF([
        QPointF(2, 2), QPointF(3, 25), QPointF(9, 20), QPointF(14, 30),
        QPointF(19, 28), QPointF(14, 18), QPointF(22, 18),
    ]))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#59D9B0"))
    painter.drawPolygon(QPolygonF([QPointF(6, 10), QPointF(7, 19), QPointF(10, 16), QPointF(15, 16)]))
    painter.end()
    return QCursor(pixmap, 2, 2)
