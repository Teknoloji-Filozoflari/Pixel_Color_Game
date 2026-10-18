from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QActionGroup, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from ..rendering.canvas import Canvas
from .appearance import AppearanceMenu
from .artwork_info import ArtworkInfoDialog
from .completion import CompletionOverlay
from .controls_help import ControlsButton, ControlsDialog
from .i18n import number, painting_meaning, painting_title, percentage, tr
from .recording import RecordingMenu
from .view_actions import HIGHLIGHTS, ViewButton
from .widgets import FillButton, GameActionButton, HintButton, Minimap, Palette, label


class GameScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal()
    recording_export_requested = Signal()

    def __init__(self, session, settings, debug=False):
        super().__init__()
        self.session, self.settings = session, settings
        self.focus_mode = False
        self.active = True
        self.completed_announced = session.painting.progress == 1
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        self.status_header = QFrame()
        self.status_header.setObjectName("panel")
        top = QHBoxLayout(self.status_header)
        top.setContentsMargins(10, 8, 10, 8)
        top.setSpacing(8)
        display_title = painting_title(session.painting.id, session.painting.title)
        title = label(display_title, "subheading")
        title.setObjectName('gamePaintingTitle')
        title.setWordWrap(False)
        title.setMinimumWidth(40)
        title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        title.setToolTip(display_title)
        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        title_box.addWidget(title)
        if session.painting.meaning:
            meaning = label(painting_meaning(session.painting.id, session.painting.meaning), 'muted')
            meaning.setObjectName('gamePaintingMeaning')
            meaning.setWordWrap(True)
            meaning.setMinimumWidth(40)
            policy = meaning.sizePolicy()
            policy.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
            policy.setHeightForWidth(True)
            meaning.setSizePolicy(policy)
            title_box.addWidget(meaning)
        top.addLayout(title_box, 1)
        self.pixel_count_label = QPushButton()
        self.pixel_count_label.setObjectName('pixelCountSelector')
        self.pixel_count_label.setAccessibleName(tr("Gösterilecek piksel sayısını seç"))
        menu = QMenu(self.pixel_count_label)
        group = QActionGroup(menu)
        group.setExclusive(True)
        self.pixel_count_actions = {}
        if settings.get('pixel_count_mode') not in ('selected', 'image'):
            settings['pixel_count_mode'] = 'selected'
        for mode, caption in [('selected', tr('Seçili renk: boyanan / toplam piksel')),
                              ('image', tr('Tüm resim: boyanan / toplam piksel'))]:
            action = menu.addAction(caption)
            action.setCheckable(True)
            action.setChecked(settings['pixel_count_mode'] == mode)
            group.addAction(action)
            action.triggered.connect(lambda checked=False, selected=mode: self.set_pixel_count_mode(selected))
            self.pixel_count_actions[mode] = action
        self.pixel_count_label.setMenu(menu)
        top.addWidget(self.pixel_count_label)
        top.addSpacing(12)
        self.progress_label = label('', 'statusValue')
        self.progress_label.setWordWrap(False)
        self.progress_label.setToolTip(tr('Boyanan alan yüzdesi'))
        self.progress_label.setAccessibleName(tr('Boyanan alan yüzdesi'))
        top.addWidget(self.progress_label)
        root.addWidget(self.status_header)
        body = QHBoxLayout()
        self.canvas = Canvas(session, settings, debug)
        body.addWidget(self.canvas, 1)
        sidebar = QWidget()
        self.painting_sidebar = sidebar
        panels = QVBoxLayout(sidebar)
        panels.setContentsMargins(0, 0, 0, 0)
        panels.setSpacing(16)
        self.preview_panel = QFrame()
        self.preview_panel.setObjectName("panel")
        preview_layout = QVBoxLayout(self.preview_panel)
        preview_layout.setContentsMargins(15, 16, 15, 16)
        preview_layout.addWidget(label(tr("BOYAMA DURUMU"), "eyebrow"))
        self.minimap = Minimap(self.canvas)
        self.preview_panel.setFixedWidth(self.minimap.width() + 30)
        preview_layout.addWidget(self.minimap)
        panels.addWidget(self.preview_panel, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.palette_panel = QFrame()
        self.palette_panel.setObjectName("panel")
        side = QVBoxLayout(self.palette_panel)
        side.setContentsMargins(15, 16, 15, 16)
        side.addWidget(label(tr("RENK PALETİ"), "eyebrow"))
        side.addWidget(label(tr("Bir numara seç, eşleşen hücreleri boya."), "muted"))
        self.palette = Palette(session)
        scroll = QScrollArea()
        self.palette_scroll = scroll
        # Reserve scrollbar space so the fifth palette column is never clipped.
        sidebar.setFixedWidth(
            self.palette.width() + 34 + scroll.style().pixelMetric(QStyle.PixelMetric.PM_ScrollBarExtent)
        )
        scroll.setWidget(self.palette)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        side.addWidget(scroll, 1)
        self.fill_button = FillButton()
        self.fill_button.toggled.connect(self.set_fill_mode)
        self.hint_button = HintButton()
        self.hint_button.toggled.connect(self.show_remaining)
        panels.addWidget(self.palette_panel, 1)
        body.addWidget(sidebar)
        root.addLayout(body, 1)
        tools = QHBoxLayout()
        tools.setSpacing(5)
        self.home_button = GameActionButton("home", self.back_requested.emit)
        self.save_button = GameActionButton("save", self.save_requested.emit)
        self.controls_button = ControlsButton(self.show_controls)
        self.grid_button = ViewButton("grid", tr("Izgara · G"))
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(settings.get("grid", True))
        self.grid_button.clicked.connect(self.toggle_grid)
        self.highlight_button = ViewButton("highlight", tr("Boyanacak alanların rengi"))
        self.highlight_button.tint = QColor(*self.canvas.cache.highlight_color)
        self.highlight_button.clicked.connect(self.cycle_highlight_color)
        self.fullscreen_button = ViewButton("fullscreen", tr("Yalnızca resim · F11 (çıkış: Esc)"))
        self.fullscreen_button.clicked.connect(self.toggle_focus_mode)
        self.appearance_button = ViewButton('appearance', tr('Görünüm ayarları'))
        self.appearance_menu = AppearanceMenu(settings, self.appearance_button)
        self.appearance_menu.changed.connect(self.appearance_changed)
        self.appearance_button.setMenu(self.appearance_menu)
        self.recording_button = ViewButton('recording', tr('Boyama kaydı · GIF'))
        self.recording_button.setCheckable(True)
        self.recording_menu = RecordingMenu(self.canvas, self.recording_button)
        self.recording_menu.export_requested.connect(self.recording_export_requested.emit)
        self.recording_button.setMenu(self.recording_menu)
        self.info_button = ViewButton('info', tr('Resim hakkında'))
        self.info_button.clicked.connect(self.show_artwork_info)
        for tool in (self.home_button, self.save_button, self.fill_button, self.hint_button,
                     self.controls_button, self.grid_button, self.highlight_button,
                     self.appearance_button, self.recording_button, self.info_button, self.fullscreen_button):
            tool.setFixedSize(42, 40)
            tools.addWidget(tool)
        top.insertLayout(0, tools)
        self.palette.selected.connect(self.select)
        self.canvas.color_picked.connect(self.select)
        self.canvas.changed.connect(self.refresh)
        self.canvas.stroke_finished.connect(self.stroke_done)
        for keys, callback in [
            ("Ctrl+S", self.save_requested.emit),
            ("F", self.canvas.fit),
            ("G", self.toggle_grid),
            ("M", self.toggle_minimap),
            ("F11", self.toggle_focus_mode),
            ("Escape", self.exit_focus_mode),
            ("Left", lambda: self.canvas.pan_cells(-1, 0)),
            ("Right", lambda: self.canvas.pan_cells(1, 0)),
            ("Up", lambda: self.canvas.pan_cells(0, -1)),
            ("Down", lambda: self.canvas.pan_cells(0, 1)),
        ]:
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(callback)
        self.refresh()

    def appearance_changed(self):
        self.grid_button.setChecked(self.settings.get('grid', True))
        self.canvas.update()

    def show_artwork_info(self):
        self.canvas.finish_stroke()
        dialog = ArtworkInfoDialog(self.session.painting, self)
        dialog.exec()
        dialog.deleteLater()
        self.canvas.setFocus()

    def dispose(self):
        self.active = False
        self.recording_menu.pause()
        for overlay in self.canvas.findChildren(CompletionOverlay):
            overlay.cancel()

    def hideEvent(self, event):
        for overlay in self.canvas.findChildren(CompletionOverlay):
            overlay.cancel()
        self.recording_menu.pause()
        super().hideEvent(event)

    def show_controls(self):
        self.canvas.finish_stroke()
        self.canvas.panning = False
        ControlsDialog(self).exec()
        self.canvas.setFocus()

    def select(self, i):
        self.canvas.select(i)
        self.refresh()
        self.ensure_selected_visible()
        self.canvas.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self.ensure_selected_visible()

    def ensure_selected_visible(self):
        slot = self.session.color_numbers[self.session.selected] - 1
        cell = self.palette.cell
        self.palette_scroll.ensureVisible(
            slot % self.palette.columns * cell + cell // 2,
            slot // self.palette.columns * cell + cell // 2,
            cell // 2, cell // 2,
        )

    def set_fill_mode(self, enabled):
        self.canvas.finish_stroke()
        self.canvas.fill_mode = enabled
        self.canvas.setFocus()

    def show_remaining(self, enabled):
        if enabled:
            self.minimap.show()
        self.minimap.set_remaining(enabled)

    def refresh(self):
        p = self.session.painting
        self.progress_label.setText(percentage(p.progress * 100))
        if self.settings['pixel_count_mode'] == 'image':
            painted, total = p.painted_count, p.target_map.size
            caption = tr('Tüm resim: boyanan / toplam piksel')
        else:
            painted = int(p.counts[self.session.selected])
            total = int(p.totals[self.session.selected])
            caption = tr('Seçili renk: boyanan / toplam piksel')
        self.pixel_count_label.setText(f'{number(painted)} / {number(total)}')
        self.pixel_count_label.setToolTip(caption)
        self.palette.update()

    def set_pixel_count_mode(self, mode):
        if mode not in self.pixel_count_actions:
            return
        self.settings['pixel_count_mode'] = mode
        self.pixel_count_actions[mode].setChecked(True)
        self.refresh()

    def stroke_done(self):
        p = self.session.painting
        selected = self.session.selected
        if p.counts[selected] >= p.totals[selected]:
            following = self.session.next_unfinished_color(after=selected)
            if following is not None:
                self.select(following)
        self.refresh()
        if self.session.painting.progress == 1 and not self.completed_announced:
            self.completed_announced = True
            self.save_requested.emit()
            if self.settings.get("sound", False):
                QApplication.beep()
            QTimer.singleShot(0, self.show_completion)

    def show_completion(self):
        if not self.active or not self.isVisible() or self.session.painting.progress < 1:
            return
        if any(not overlay.ended for overlay in self.canvas.findChildren(CompletionOverlay)):
            return
        if self.recording_menu.recorder.active:
            self.recording_menu.recorder.capture(force=True)
        overlay = CompletionOverlay(self.canvas, animate=self.settings.get('completion_animation', True))
        overlay.collection_requested.connect(self.back_requested.emit)

    def toggle_grid(self):
        self.settings["grid"] = not self.settings.get("grid", True)
        self.grid_button.setChecked(self.settings["grid"])
        self.canvas.update()

    def toggle_minimap(self):
        self.minimap.setVisible(not self.minimap.isVisible())

    def cycle_highlight_color(self):
        colors = list(HIGHLIGHTS.values())
        current = tuple(self.canvas.cache.highlight_color)
        index = colors.index(current) if current in colors else -1
        self.set_highlight_color(colors[(index + 1) % len(colors)])

    def set_highlight_color(self, color):
        self.settings["highlight_color"] = color
        self.canvas.cache.highlight_color = color
        self.canvas.cache.clear()
        self.highlight_button.tint = QColor(*color)
        self.highlight_button.update()
        self.canvas.update()
        self.canvas.setFocus()

    def toggle_focus_mode(self):
        if self.focus_mode:
            self.exit_focus_mode()
            return
        self.canvas.finish_stroke()
        window = self.window()
        self.previous_window_state = window.windowState()
        self.hidden_panels = [self.status_header, self.painting_sidebar]
        if window is not self and hasattr(window, "statusBar"):
            self.hidden_panels.append(window.statusBar())
        self.panel_visibility = [not panel.isHidden() for panel in self.hidden_panels]
        for panel in self.hidden_panels:
            panel.hide()
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.focus_mode = True
        window.showFullScreen()
        self.canvas.setFocus()

    def exit_focus_mode(self):
        self.canvas.finish_stroke()
        self.canvas.panning = False
        self.canvas.setCursor(self.canvas.painting_cursor)
        if not self.focus_mode:
            return
        self.focus_mode = False
        for panel, visible in zip(self.hidden_panels, self.panel_visibility):
            panel.setVisible(visible)
        self.layout().setContentsMargins(20, 14, 20, 14)
        self.window().setWindowState(self.previous_window_state)
        self.canvas.setFocus()
