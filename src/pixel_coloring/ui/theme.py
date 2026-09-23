STYLE = """
QWidget { background: #23272E; color: #E6E6E6; font-family: 'Noto Sans'; font-size: 13px; }
QMainWindow, QStackedWidget { background: #23272E; }
QLabel { background: transparent; }
QLabel#eyebrow { color: #F3946F; font-size: 11px; font-weight: 700; letter-spacing: 2px; }
QLabel#heading { font-size: 34px; font-weight: 700; }
QLabel#subheading { font-size: 19px; font-weight: 600; }
QLabel#muted { color: #9CA5B1; }
QLabel#statusValue { color: #D4F2E7; font-size: 15px; font-weight: 600; }
QFrame#panel { background: #2D333B; border: 1px solid #3C434D; border-radius: 12px; }
QPushButton { background: #343B45; border: 1px solid #48505B; border-radius: 7px; padding: 9px 14px; }
QPushButton:hover { background: #414B58; border-color: #78818C; }
QPushButton:pressed { background: #242A32; }
QPushButton:checked { background: #AAF5B9; border: 2px solid #DBFFE2; }
QPushButton:focus { border: 2px solid #F3946F; }
QPushButton:disabled { color: #6E7682; background: #2B3038; border-color: #343B45; }
QPushButton#primary { background: #F06C3B; color: #171D25; border: 0; font-weight: 700; padding: 12px 22px; }
QPushButton#primary:hover { background: #FF8658; }
QPushButton#nav { text-align: left; padding: 12px 18px; background: transparent; border: 0; color: #B0B8C2; }
QPushButton#nav:checked { color: #FFC6AC; background: #45352F; border-left: 3px solid #F06C3B; }
QLineEdit, QComboBox, QSpinBox { background: #1E242C; border: 1px solid #48505B; border-radius: 6px; padding: 8px; }
QProgressBar { background: #1E242C; border: 0; border-radius: 4px; height: 7px; text-align: center; }
QProgressBar::chunk { background: #F06C3B; border-radius: 4px; }
QScrollArea { border: 0; background: transparent; }
QScrollBar:vertical { background: #23272E; width: 9px; }
QScrollBar::handle:vertical { background: #515A67; border-radius: 4px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #3B4350; color: white; border: 1px solid #6A7484; padding: 6px; }
QCheckBox { spacing: 10px; padding: 7px; }
QStatusBar { color: #9CA5B1; font-size: 11px; }
QFrame#settingsCard { background: #2D333B; border: 1px solid #414A56; border-radius: 16px; }
QFrame#settingsCard QCheckBox { background: transparent; }
QPushButton#intervalChoice { background: #222831; color: #B9C3D0; border: 1px solid #485362;
    border-radius: 9px; padding: 10px 12px; }
QPushButton#intervalChoice:checked { background: #F3946F; color: #20252D; border-color: #F3946F;
    font-weight: 700; }
QPushButton#intervalChoice:hover { border-color: #FFD1BC; }
QPushButton#intervalChoice:focus { border: 2px solid #FFE2D5; }
QLabel#settingPercent { background: #223D3C; color: #93E1CF; border-radius: 7px; padding: 5px; }
QSlider#settingSlider { background: transparent; }
QSlider#settingSlider::groove:horizontal { height: 6px; background: #1C232C; border-radius: 3px; }
QSlider#settingSlider::sub-page:horizontal { background: #77CBB9; border-radius: 3px; }
QSlider#settingSlider::handle:horizontal { background: #D3F5EB; border: 3px solid #77CBB9;
    width: 14px; height: 14px; margin: -7px 0; border-radius: 10px; }
QSlider#settingSlider::handle:horizontal:hover, QSlider#settingSlider::handle:horizontal:focus {
    background: white; border-color: #F3946F; }
"""


def apply_theme(app):
    from pathlib import Path

    from PySide6.QtGui import QFont, QFontDatabase

    font = Path(__file__).resolve().parents[1] / "resources/fonts/NotoSans.ttf"
    if font.exists():
        QFontDatabase.addApplicationFont(str(font))
    app.setFont(QFont("Noto Sans", 10))
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
