from PySide6.QtCore import QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from ..importer.level_writer import read_level
from ..rendering.tile_cache import rgb_image
from .home_actions import HomeAction
from .i18n import LANGUAGES, number, painting_meaning, painting_title, tr
from .progress_tile import ProgressTile
from .widgets import ResponsiveGrid, button, label

DIFFICULTIES = [
    'Çok Kolay', 'Kolay', 'Kolay-Orta', 'Orta', 'Orta-Zor', 'Zor', 'Uzman',
]
STATUS_FILTERS = [
    ('all', 'Tümü'),
    ('not_started', 'Başlanmamış'),
    ('in_progress', 'Devam eden'),
    ('completed', 'Tamamlanan'),
    ('favorites', 'Favoriler'),
]
SORT_OPTIONS = [
    ('catalog', 'Katalog sırası'),
    ('difficulty', 'Zorluk'),
    ('progress', 'İlerleme'),
    ('recent', 'Son oynanan'),
]


class CategoryBar(QFrame):
    resized = Signal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


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


def _compact_combo(object_name, accessible):
    widget = QComboBox()
    widget.setObjectName(object_name)
    widget.setAccessibleName(accessible)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.setFixedHeight(32)
    widget.setMinimumWidth(168)
    widget.setStyleSheet('''
        QComboBox {background:#263C3B; color:#D4E8E2; border:1px solid #52786D;
            border-radius:8px; padding:0 10px; font-size:12px; font-weight:600;}
        QComboBox:hover {background:#315048; border-color:#85C7AD;}
        QComboBox:focus {border:2px solid #F3946F;}
        QComboBox::drop-down {border:0; width:22px;}
        QComboBox QAbstractItemView {background:#263238; color:#E5F1ED;
            selection-background-color:#315B51; padding:4px; border:1px solid #52786D;}
    ''')
    return widget


class FilterMenu(QMenu):
    changed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        panel = QWidget(self)
        panel.setObjectName('filterMenuPanel')
        panel.setStyleSheet('''
            QWidget#filterMenuPanel {background:#1C2928; border:1px solid #496B62; border-radius:12px;}
            QLabel {color:#AEB9C4; font-size:11px; font-weight:600;}
        ''')
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)

        self.difficulty = _compact_combo('difficultyFilter', tr('Zorluk'))
        self.difficulty.addItem(tr('Tüm zorluklar'), '')
        for name in DIFFICULTIES:
            self.difficulty.addItem(tr(name), name)
        self.difficulty.setCurrentIndex(
            max(0, self.difficulty.findData(settings.get('collection_difficulty', '')))
        )

        self.status = _compact_combo('statusFilter', tr('Durum'))
        for key, caption in STATUS_FILTERS:
            self.status.addItem(tr(caption), key)
        self.status.setCurrentIndex(
            max(0, self.status.findData(settings.get('collection_status', 'all')))
        )

        self.sort = _compact_combo('sortFilter', tr('Sıralama'))
        for key, caption in SORT_OPTIONS:
            self.sort.addItem(tr(caption), key)
        self.sort.setCurrentIndex(
            max(0, self.sort.findData(settings.get('collection_sort', 'catalog')))
        )

        for caption, combo in (
            (tr('Zorluk'), self.difficulty),
            (tr('Durum'), self.status),
            (tr('Sıralama'), self.sort),
        ):
            layout.addWidget(label(caption, 'muted'))
            layout.addWidget(combo)

        action = QWidgetAction(self)
        action.setDefaultWidget(panel)
        self.addAction(action)
        for combo in (self.difficulty, self.status, self.sort):
            # currentIndexChanged carries an int; wrap so the no-arg signal still fires.
            combo.currentIndexChanged.connect(lambda *_: self.changed.emit())
            combo.activated.connect(lambda *_: self.changed.emit())

    def is_active(self):
        return (
            bool(self.difficulty.currentData())
            or self.status.currentData() != 'all'
            or self.sort.currentData() != 'catalog'
        )


def build_collection(window, root):
    favorites = set(window.settings.get('favorites') or [])
    window.settings['favorites'] = sorted(favorites)
    if window.settings.get('collection_status') not in {key for key, _ in STATUS_FILTERS}:
        window.settings['collection_status'] = 'all'
    if window.settings.get('collection_sort') not in {key for key, _ in SORT_OPTIONS}:
        window.settings['collection_sort'] = 'catalog'
    if window.settings.get('collection_difficulty') not in (None, '', *DIFFICULTIES):
        window.settings['collection_difficulty'] = ''

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

    filter_button = HomeAction('filter', tr('Filtreler'), None)
    filter_menu = FilterMenu(window.settings, filter_button)
    filter_button.setMenu(filter_menu)
    head.addWidget(filter_button, alignment=Qt.AlignmentFlag.AlignVCenter)

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
    add_button = HomeAction('add', tr('Resim ekle'), None)
    add_button.setMenu(window.import_menu(add_button))
    head.addWidget(add_button)
    head.addWidget(HomeAction('settings', tr('Ayarlar'), window.show_settings))
    head.addWidget(HomeAction('exit', tr('Çıkış'), window.close))
    root.addWidget(hero)
    categories = ['Tüm kategoriler', 'Doğa', 'Hayvanlar', 'Fantastik', 'Manzaralar',
                  'Şehirler', 'TÜRKİYE', 'TÜRK MOTİFLERİ', 'Harikalar', 'Teknoloji', 'Araçlar', 'İçe aktarılan']
    if window.collection_category not in categories:
        window.collection_category = categories[0]
    category_bar = CategoryBar()
    category_bar.setObjectName('categoryBar')
    category_bar.setStyleSheet('''
        QFrame#categoryBar {background:#1C2229; border:1px solid #39424A; border-radius:12px;}
        QPushButton#categoryTab {background:transparent; color:#AEB9C4; border:0;
            border-radius:8px; padding:11px 10px; font-weight:600;}
        QPushButton#categoryTab:hover {background:#303C43; color:#F0F5F3;}
        QPushButton#categoryTab:checked {background:#315B51; color:#DCFFF0; border:1px solid #639789;}
        QPushButton#categoryTab:focus {border:1px solid #F0784F;}
    ''')
    category_row = QGridLayout(category_bar)
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
        category_row.addWidget(tab, 0, len(window.category_buttons) - 1)
    category_columns = None
    tabs = list(window.category_buttons.values())

    def arrange_categories():
        nonlocal category_columns
        required = sum(tab.sizeHint().width() for tab in tabs) + 5 * (len(tabs) - 1) + 12
        columns = len(tabs) if category_bar.width() >= required else (len(tabs) + 1) // 2
        if columns == category_columns:
            return
        category_columns = columns
        for tab in tabs:
            category_row.removeWidget(tab)
        for column in range(len(tabs)):
            category_row.setColumnStretch(column, 1 if column < columns else 0)
        for index, tab in enumerate(tabs):
            category_row.addWidget(tab, index // columns, index % columns)

    category_bar.resized.connect(arrange_categories)
    arrange_categories()
    root.addWidget(category_bar)

    difficulty = filter_menu.difficulty
    status = filter_menu.status
    sort = filter_menu.sort

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
    progress = window.database.progress_map()

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

    def sync_filter_button():
        active = filter_menu.is_active()
        filter_button.setProperty('filtersActive', active)
        filter_button.setToolTip(
            tr('Filtreler · seçili') if active else tr('Filtreler')
        )
        filter_button.setAccessibleName(filter_button.toolTip())
        filter_button.update()

    def toggle_favorite(chosen):
        current = set(window.settings.get('favorites') or [])
        if chosen in current:
            current.remove(chosen)
        else:
            current.add(chosen)
        window.settings['favorites'] = sorted(current)
        try:
            window.database.set_settings({'favorites': window.settings['favorites']})
        except Exception:
            pass
        arrange(force=True)
        if window.collection_selected == chosen:
            select(chosen)

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
        if p.meaning:
            meaning = label(painting_meaning(p.id, p.meaning), 'muted')
            meaning.setObjectName('paintingMeaning')
            meaning.setWordWrap(True)
            detail_box.addWidget(meaning)
        window.database.load(p)
        rgb = p.palette[p.target_map].copy()
        gray = (rgb.mean(axis=2) * .2 + 155).astype('uint8')
        rgb[~p.painted_mask] = gray[~p.painted_mask, None]
        preview = CollectionPreview(QPixmap.fromImage(rgb_image(rgb)))
        detail_box.addWidget(preview, 1)
        info = QFrame()
        info.setStyleSheet('QFrame {background:#216F65; border-radius:10px;}')
        info_box = QVBoxLayout(info)
        meta = window.level_details.get(chosen, {})
        difficulty_name = meta.get('difficulty')
        lines = [f'{width} × {height}   ·   {number(width*height)} px']
        if difficulty_name:
            lines.append(tr(difficulty_name))
        dimensions = label('\n'.join(lines))
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
        favorited = chosen in set(window.settings.get('favorites') or [])
        favorite_caption = tr('Favoriden çıkar') if favorited else tr('Favorilere ekle')
        detail_box.addWidget(button(favorite_caption, lambda: toggle_favorite(chosen)))
        action = tr('Baştan başla') if p.progress == 1 else (tr('Devam et') if p.painted_count else tr('Boyamaya başla'))
        detail_box.addWidget(button(action, lambda: window.restart_painting(chosen) if p.progress == 1 else window.open_painting(chosen), True))
        detail_box.addWidget(button(tr('Önizle'), lambda: window.preview_painting(chosen)))
        if p.progress == 1:
            detail_box.addWidget(button(tr('Resmi indir'), lambda: window.export_completed(chosen)))
        if not chosen.startswith('sample-'):
            detail_box.addWidget(button(tr('Resmi sil'), lambda: window.delete_painting(chosen)))

    for key, (title, cat, *_rest) in window.metadata.items():
        display_title = painting_title(key, title)
        percent = progress.get(key, (0,))[0]
        tile = ProgressTile(percent)
        tile.setCheckable(True)
        tile.setStyleSheet('QPushButton:checked {background:#315B51; border:2px solid #8BC9B5;}')
        tile.setFixedSize(96, 92)
        tile.setIconSize(QSize(78, 72))
        status_text = tr('Bitti') if percent >= 100 else tr('%{percent} boyandı', percent=number(percent, 1))
        tile.setToolTip(display_title + ' · ' + status_text)
        tile.setAccessibleName(display_title + ' · ' + status_text)
        meta = window.level_details.get(key, {})
        tile.setProperty('level_order', meta.get('order', 10**9))
        tile.setProperty('level_tier', meta.get('tier', 99))
        tile.setProperty('level_difficulty', meta.get('difficulty', ''))
        tile.setProperty('level_category', cat)
        tile.setProperty('progress_percent', float(percent or 0))
        tile.setProperty('last_played', float((progress.get(key) or (0, 0, 0, 0))[3] or 0))
        tile.clicked.connect(lambda checked=False, chosen=key: select(chosen))
        tiles.append((tile, key, cat))

    last_arrangement = None

    def matches(key, cat, tile):
        if window.collection_category not in ('Tüm kategoriler', cat):
            return False
        wanted_difficulty = difficulty.currentData()
        if wanted_difficulty and tile.property('level_difficulty') != wanted_difficulty:
            return False
        percent = float(tile.property('progress_percent') or 0)
        status_key = status.currentData()
        favorited = key in set(window.settings.get('favorites') or [])
        if status_key == 'not_started' and percent > 0:
            return False
        if status_key == 'in_progress' and not (0 < percent < 100):
            return False
        if status_key == 'completed' and percent < 100:
            return False
        if status_key == 'favorites' and not favorited:
            return False
        return True

    def sort_key(item):
        tile, key, cat = item
        mode = sort.currentData()
        if mode == 'difficulty':
            return (tile.property('level_tier') or 99, tile.property('level_order') or 10**9, key)
        if mode == 'progress':
            return (-float(tile.property('progress_percent') or 0), tile.property('level_order') or 10**9, key)
        if mode == 'recent':
            return (-float(tile.property('last_played') or 0), tile.property('level_order') or 10**9, key)
        return (cat, tile.property('level_order') or 10**9, key)

    def arrange(force=False):
        nonlocal last_arrangement
        visible = [(t, k) for t, k, c in sorted(tiles, key=sort_key) if matches(k, c, t)]
        columns = max(1, scroll.viewport().width() // 108)
        arrangement = (columns, status.currentData(), difficulty.currentData(), sort.currentData(),
                       window.collection_category, tuple(key for _, key in visible))
        if not force and arrangement == last_arrangement:
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
            detail_box.addWidget(label(tr('Bu filtreyle eşleşen resim yok.'), 'subheading'))
            if window.collection_category == 'İçe aktarılan':
                detail_box.addWidget(button(tr('Resim ekle'), window.import_dialog, True))
        if visible and window.collection_selected not in [key for _, key in visible]:
            select(visible[0][1])
        icon_timer.start(0)

    def persist_filters():
        window.settings['collection_difficulty'] = difficulty.currentData() or ''
        window.settings['collection_status'] = status.currentData()
        window.settings['collection_sort'] = sort.currentData()
        try:
            window.database.set_settings({
                'collection_difficulty': window.settings['collection_difficulty'],
                'collection_status': window.settings['collection_status'],
                'collection_sort': window.settings['collection_sort'],
            })
        except Exception:
            pass
        sync_filter_button()
        # Apply to the current category immediately, even if the popup is still closing.
        arrange(force=True)

    filter_menu.changed.connect(lambda: QTimer.singleShot(0, persist_filters))
    sync_filter_button()

    def category_changed(name):
        window.collection_category = name
        arrange(force=True)
    for name, tab in window.category_buttons.items():
        tab.clicked.connect(lambda checked=False, selected=name: category_changed(selected))
    container.resized.connect(arrange)
    scroll.viewport_resized.connect(arrange)
    previous_selection = window.collection_selected
    arrange(force=True)
    if previous_selection == window.collection_selected and window.collection_selected in window.paths:
        select(window.collection_selected)
