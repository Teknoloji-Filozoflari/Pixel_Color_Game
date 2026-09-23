from PySide6.QtCore import QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..importer.level_writer import read_level
from ..rendering.tile_cache import rgb_image
from .home_actions import HomeAction
from .i18n import LANGUAGES, number, tr, painting_title
from .progress_tile import ProgressTile
from .widgets import ResponsiveGrid, button, label


class LanguageSelector(QComboBox):
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = painter.pen()
        pen.setColor(QColor('#D4E8E2'))
        pen.setWidth(2)
        painter.setPen(pen)
        x, y = self.width() - 18, self.height() // 2
        painter.drawLine(x - 4, y - 2, x, y + 2)
        painter.drawLine(x, y + 2, x + 4, y - 2)
        painter.end()


class CollectionScrollArea(QScrollArea):
    viewport_resized = Signal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.viewport_resized.emit)


class CollectionPreview(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.pixmap = pixmap
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        size = self.pixmap.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        target = QRect((self.width()-size.width())//2, (self.height()-size.height())//2,
                       size.width(), size.height())
        painter = QPainter(self)
        painter.drawPixmap(target, self.pixmap)
        painter.end()


def build_collection(window, root):
    hero = QFrame()
    hero.setObjectName('panel')
    head = QHBoxLayout(hero)
    head.setContentsMargins(24, 18, 24, 18)
    brand = QVBoxLayout()
    brand.setSpacing(4)
    logo = label('PİKSEL ATÖLYESİ', 'heading')
    logo.setStyleSheet('color:#F0784F; font-size:30px; font-weight:800;')
    brand.addWidget(logo)
    brand.addWidget(label(tr('Bir resim seç. Renklerle tamamla.'), 'muted'))
    head.addLayout(brand, 1)
    language_combo = LanguageSelector()
    language_combo.setObjectName('languageSelector')
    language_combo.setAccessibleName(tr('Dil'))
    language_combo.setToolTip(tr('Dil'))
    language_combo.setFixedSize(158, 44)
    language_combo.setCursor(Qt.CursorShape.PointingHandCursor)
    language_combo.setStyleSheet('''
        QComboBox#languageSelector {background:#263C3B; color:#D4E8E2;
            border:1px solid #52786D; border-radius:10px; padding:0 14px; font-weight:600;}
        QComboBox#languageSelector:hover {background:#315048; border-color:#85C7AD;}
        QComboBox#languageSelector:focus {border:2px solid #F3946F;}
        QComboBox#languageSelector::drop-down {border:0; width:26px;}
        QComboBox QAbstractItemView {background:#263238; color:#E5F1ED;
            selection-background-color:#315B51; padding:6px; border:1px solid #52786D;}
    ''')
    for code, native_name in LANGUAGES.items():
        language_combo.addItem(native_name, code)
    language_combo.setCurrentIndex(language_combo.findData(window.settings['language']))
    head.addWidget(language_combo, alignment=Qt.AlignmentFlag.AlignVCenter)
    window.language_combo = language_combo
    language_combo.currentIndexChanged.connect(lambda index: window.change_language(language_combo.itemData(index)))
    head.addWidget(HomeAction('add', tr('Resim ekle'), window.import_dialog))
    head.addWidget(HomeAction('settings', tr('Ayarlar'), window.show_settings))
    head.addWidget(HomeAction('exit', tr('Çıkış'), window.close))
    root.addWidget(hero)
    categories = ['Tüm kategoriler', 'Doğa', 'Hayvanlar', 'Fantastik', 'Manzaralar',
                  'Şehirler', 'TÜRKİYE', 'İçe aktarılan']
    if window.collection_category not in categories:
        window.collection_category = categories[0]
    category_bar = QFrame()
    category_bar.setObjectName('categoryBar')
    category_bar.setStyleSheet('''
        QFrame#categoryBar {background:#1C2229; border:1px solid #39424A; border-radius:12px;}
        QPushButton#categoryTab {background:transparent; color:#AEB9C4; border:0;
            border-radius:8px; padding:11px 10px; font-weight:600;}
        QPushButton#categoryTab:hover {background:#303C43; color:#F0F5F3;}
        QPushButton#categoryTab:checked {background:#315B51; color:#DCFFF0; border:1px solid #639789;}
        QPushButton#categoryTab:focus {border:1px solid #F0784F;}
    ''')
    category_row = QHBoxLayout(category_bar)
    category_row.setContentsMargins(6, 6, 6, 6)
    category_row.setSpacing(5)
    group = QButtonGroup(category_bar)
    group.setExclusive(True)
    window.category_buttons = {}
    for name in categories:
        caption = 'Tümü' if name == 'Tüm kategoriler' else ('Yüklenenler' if name == 'İçe aktarılan' else name)
        tab = QPushButton(tr(caption))
        tab.setObjectName('categoryTab')
        tab.setAccessibleName(tr(caption))
        tab.setCheckable(True)
        tab.setChecked(name == window.collection_category)
        tab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tab.setCursor(Qt.CursorShape.PointingHandCursor)
        group.addButton(tab)
        window.category_buttons[name] = tab
        category_row.addWidget(tab)
    root.addWidget(category_bar)
    content = QHBoxLayout()
    content.setSpacing(22)
    details = QFrame()
    details.setObjectName('panel')
    details.setFixedWidth(410)
    detail_box = QVBoxLayout(details)
    detail_box.setContentsMargins(20, 20, 20, 20)
    root.addLayout(content, 1)
    content.addWidget(details)
    scroll = CollectionScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    container = ResponsiveGrid()
    grid = QGridLayout(container)
    grid.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
    grid.setAlignment(Qt.AlignmentFlag.AlignTop)
    grid.setSpacing(10)
    scroll.setWidget(container)
    content.addWidget(scroll, 1)
    tiles = []
    loaded_icons = set()
    icon_timer = QTimer(container)
    icon_timer.setSingleShot(True)

    def load_visible_icons():
        viewport = scroll.viewport().rect()
        pending = [(tile, key) for tile, key, _ in tiles
                   if key not in loaded_icons and not tile.isHidden()
                   and QRect(tile.mapTo(scroll.viewport(), tile.rect().topLeft()), tile.size()).intersects(viewport)]
        for tile, key in pending[:12]:
            tile.setIcon(QIcon(window.thumbnail(key, 78, 72)))
            loaded_icons.add(key)
        if len(pending) > 12:
            icon_timer.start(0)

    icon_timer.timeout.connect(load_visible_icons)
    scroll.verticalScrollBar().valueChanged.connect(lambda _: icon_timer.start(0))

    def select(chosen):
        window.collection_selected = chosen
        for tile, key, _ in tiles:
            tile.setChecked(key == chosen)
        while detail_box.count():
            item = detail_box.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        title, _, width, height, _ = window.metadata[chosen]
        heading = label(painting_title(chosen, title), 'subheading')
        heading.setObjectName('paintingTitle')
        detail_box.addWidget(heading)
        p = read_level(window.paths[chosen])
        window.database.load(p)
        rgb = p.palette[p.target_map].copy()
        gray = (rgb.mean(axis=2) * .2 + 155).astype('uint8')
        rgb[~p.painted_mask] = gray[~p.painted_mask, None]
        preview = CollectionPreview(QPixmap.fromImage(rgb_image(rgb)))
        detail_box.addWidget(preview, 1)
        info = QFrame()
        info.setStyleSheet('QFrame {background:#216F65; border-radius:10px;}')
        info_box = QVBoxLayout(info)
        dimensions = label(f'{width} × {height}   ·   {number(width*height)} px')
        dimensions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_box.addWidget(dimensions)
        palette = QPixmap(320, max(1, (len(p.palette)+15)//16)*20)
        palette.fill(QColor('#216F65'))
        painter = QPainter(palette)
        for i, color in enumerate(p.palette):
            painter.fillRect((i%16)*20, (i//16)*20, 20, 20, QColor(*map(int, color)))
        painter.end()
        colors = label('')
        colors.setPixmap(palette)
        colors.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_box.addWidget(colors)
        detail_box.addWidget(info)
        action = tr('Baştan başla') if p.progress == 1 else (tr('Devam et') if p.painted_count else tr('Boyamaya başla'))
        detail_box.addWidget(button(action, lambda: window.restart_painting(chosen) if p.progress == 1 else window.open_painting(chosen), True))
        detail_box.addWidget(button(tr('Önizle'), lambda: window.preview_painting(chosen)))
        if p.progress == 1:
            detail_box.addWidget(button(tr('Resmi indir'), lambda: window.export_completed(chosen)))
        if not chosen.startswith('sample-'):
            detail_box.addWidget(button(tr('Resmi sil'), lambda: window.delete_painting(chosen)))

    progress = window.database.progress_map()
    for key, (title, cat, *_rest) in window.metadata.items():
        title = painting_title(key, title)
        percent = progress.get(key, (0,))[0]
        tile = ProgressTile(percent)
        tile.setCheckable(True)
        tile.setStyleSheet('QPushButton:checked {background:#315B51; border:2px solid #8BC9B5;}')
        tile.setFixedSize(96, 92)
        tile.setIconSize(QSize(78, 72))
        status = tr('Bitti') if percent >= 100 else tr('%{percent} boyandı', percent=number(percent, 1))
        tile.setToolTip(title + ' · ' + status)
        tile.setAccessibleName(title + ' · ' + status)
        meta = window.level_details.get(key, {})
        tile.setProperty('level_order', meta.get('order'))
        tile.setProperty('level_category', cat)
        tile.clicked.connect(lambda checked=False, chosen=key: select(chosen))
        tiles.append((tile, key, cat))

    last_arrangement = None

    def arrange():
        nonlocal last_arrangement
        visible = [(t, k) for t, k, c in tiles
                   if window.collection_category == 'Tüm kategoriler' or window.collection_category == c]
        columns = max(1, scroll.viewport().width() // 108)
        arrangement = (columns, tuple(key for _, key in visible))
        if arrangement == last_arrangement:
            if not icon_timer.isActive():
                icon_timer.start(0)
            return
        last_arrangement = arrangement
        for tile, _, _ in tiles:
            grid.removeWidget(tile)
            tile.hide()
        for i, (tile, _) in enumerate(visible):
            grid.addWidget(tile, i//columns, i%columns)
            tile.show()
        if not visible:
            window.collection_selected = None
            while detail_box.count():
                item = detail_box.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()
            detail_box.addWidget(label(tr('Bu kategoride henüz resim yok.'), 'subheading'))
            if window.collection_category == 'İçe aktarılan':
                detail_box.addWidget(button(tr('Resim ekle'), window.import_dialog, True))
        if visible and window.collection_selected not in [key for _, key in visible]:
            select(visible[0][1])
        icon_timer.start(0)

    def category_changed(name):
        window.collection_category = name
        arrange()
    for name, tab in window.category_buttons.items():
        tab.clicked.connect(lambda checked=False, selected=name: category_changed(selected))
    container.resized.connect(arrange)
    scroll.viewport_resized.connect(arrange)
    previous_selection = window.collection_selected
    arrange()
    if previous_selection == window.collection_selected and window.collection_selected in window.paths:
        select(window.collection_selected)
