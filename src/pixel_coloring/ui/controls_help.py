from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QPushButton, QTabWidget, QVBoxLayout, QWidget

from .i18n import tr
from .widgets import button, label


class ControlsButton(QPushButton):
    def __init__(self, callback):
        super().__init__()
        self.setFixedSize(48, 42)
        self.setAccessibleName(tr("Fare ve klavye kullanımı"))
        self.setToolTip(self.accessibleName())
        self.clicked.connect(callback)

    def paintEvent(self, event):
        super().paintEvent(event)
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        q.setPen(QPen(QColor("#DDE4E7"), 2))
        q.setBrush(Qt.BrushStyle.NoBrush)
        q.drawRoundedRect(QRectF(14, 5, 20, 31), 9, 9)
        q.drawLine(14, 19, 34, 19)
        q.drawLine(24, 6, 24, 13)
        q.drawRoundedRect(QRectF(22, 13, 4, 9), 2, 2)
        q.end()


class MouseDiagram(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(170, 240)
        self.setAccessibleName(tr("Sol tuş: boya; sağ tuş: renk seç; orta tuş: taşı; tekerlek: yakınlaştır"))

    def paintEvent(self, event):
        q = QPainter(self)
        q.setRenderHint(QPainter.RenderHint.Antialiasing)
        q.setPen(QPen(QColor("#DDE4E7"), 3))
        q.setBrush(QColor("#394451"))
        q.drawRoundedRect(QRectF(25, 20, 120, 195), 55, 55)
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QColor("#F3B66D"))
        q.drawRoundedRect(QRectF(35, 42, 43, 58), 12, 12)
        q.setBrush(QColor("#8BD2E8"))
        q.drawRoundedRect(QRectF(92, 42, 43, 58), 12, 12)
        q.setBrush(QColor("#ADF29F"))
        q.drawRoundedRect(QRectF(79, 50, 12, 35), 5, 5)
        q.setPen(QPen(QColor("#DDE4E7"), 2))
        q.drawLine(26, 112, 144, 112)
        q.end()


class ControlsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(tr("Fare ve klavye kullanımı"))
        self.resize(700, 530)
        root = QVBoxLayout(self)
        root.addWidget(label(tr("Kontroller"), "heading"))
        tabs = QTabWidget()
        mouse = QWidget()
        row = QHBoxLayout(mouse)
        row.addWidget(MouseDiagram())
        instructions = QVBoxLayout()
        for title, text in [
            (tr("Sol tuş"), tr("Tıkla veya basılı tutup sürükle: seçili renkte boya.")),
            (tr("Toplu boya açıkken"), tr("Sol tuşla tıkla veya sürükle: aynı renkteki bitişik alanları doldur.")),
            (tr("Sağ tuş"), tr("Tıkladığın pikselin rengini seç.")),
            (tr("Orta tuş"), tr("Basılı tutup sürükle: resmi taşı.")),
            (tr("Fare tekerleği"), tr("İmlecin olduğu yere yakınlaş veya uzaklaş.")),
            (tr("Mini harita"), tr("Gitmek istediğin yere tıkla. Ampul, kalan pikselleri kırmızı gösterir.")),
        ]:
            instructions.addWidget(label(title, "subheading"))
            instructions.addWidget(label(text, "muted"))
        row.addLayout(instructions, 1)
        tabs.addTab(mouse, tr("Fare"))
        keyboard = QWidget()
        grid = QGridLayout(keyboard)
        grid.setVerticalSpacing(16)
        for i, (key, description) in enumerate([
            (tr("Ok tuşları"), tr("Resimde gezin; basılı tutarak devam et.")),
            ("Ctrl + S", tr("Boyama ilerlemesini kaydet.")),
            ("F", tr("Resmi ekrana sığdır.")),
            ("G", tr("Izgarayı aç / kapat.")),
            ("M", tr("Mini haritayı aç / kapat.")),
            ("F11", tr("Yalnızca resim / normal görünüm.")),
            ("Esc", tr("Tam ekrandan çık; boyama veya taşımayı bitir.")),
        ]):
            cap = label(key)
            cap.setText(key)
            cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cap.setMinimumSize(125, 42)
            cap.setStyleSheet("background:#394451; color:#FFE1A6; border:2px solid #697787; border-radius:8px; font-weight:600;")
            grid.addWidget(cap, i, 0)
            grid.addWidget(label(description), i, 1)
        tabs.addTab(keyboard, tr("Klavye"))
        root.addWidget(tabs, 1)
        root.addWidget(button(tr("Kapat"), self.accept), alignment=Qt.AlignmentFlag.AlignRight)
