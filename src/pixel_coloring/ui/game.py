from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QActionGroup, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..rendering.canvas import Canvas
from .controls_help import ControlsButton, ControlsDialog
from .i18n import number, percentage, tr, painting_title
from .view_actions import HIGHLIGHTS, ViewButton
from .widgets import FillButton, GameActionButton, HintButton, Minimap, Palette, label


class GameScreen(QWidget):
    back_requested = Signal()
    save_requested = Signal()

    def __init__(self, session, settings, debug=False):
        super().__init__()
        self.session, self.settings = session, settings
        self.focus_mode = False
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
        top.addWidget(title, 1)
        self.remaining_label = label("", "statusValue")
        self.remaining_label.setWordWrap(False)
        self.remaining_label.setToolTip(tr("Seçili rengin boyanan / toplam piksel sayısı"))
        top.addWidget(self.remaining_label)
        top.addSpacing(12)
        self.progress_label = QPushButton()
        self.progress_label.setToolTip(tr("Boyanan / kalan piksel oranını seç"))
        self.progress_label.setAccessibleName(tr("Gösterilecek piksel oranı"))
        menu = QMenu(self.progress_label)
        group = QActionGroup(menu)
        group.setExclusive(True)
        self.progress_actions = {}
        for mode, caption in [('painted', tr('Boyanan pikseller')), ('remaining', tr('Kalan pikseller'))]:
            action = menu.addAction(caption)
            action.setCheckable(True)
            action.setChecked(settings.get('progress_mode', 'painted') == mode)
            group.addAction(action)
            action.triggered.connect(lambda checked=False, selected=mode: self.set_progress_mode(selected))
            self.progress_actions[mode] = action
        self.progress_label.setMenu(menu)
        top.addWidget(self.progress_label)
        root.addWidget(self.status_header)
        body = QHBoxLayout()
        self.canvas = Canvas(session, settings, debug)
        body.addWidget(self.canvas, 1)
        sidebar = QWidget()
        self.painting_sidebar = sidebar
        sidebar.setFixedWidth(262)
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
        for tool in (self.home_button, self.save_button, self.fill_button, self.hint_button,
                     self.controls_button, self.grid_button, self.highlight_button, self.fullscreen_button):
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
            ("Left", lambda: self.canvas.pan_view(-96, 0)),
            ("Right", lambda: self.canvas.pan_view(96, 0)),
            ("Up", lambda: self.canvas.pan_view(0, -96)),
            ("Down", lambda: self.canvas.pan_view(0, 96)),
        ]:
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(callback)
        self.refresh()

    def show_controls(self):
        self.canvas.finish_stroke()
        self.canvas.panning = False
        ControlsDialog(self).exec()
        self.canvas.setFocus()

    def select(self, i):
        self.canvas.select(i)
        self.refresh()

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
        ratio = 1 - p.progress if self.settings.get('progress_mode') == 'remaining' else p.progress
        self.progress_label.setText(percentage(ratio * 100))
        painted = int(p.counts[self.session.selected])
        total = int(p.totals[self.session.selected])
        self.remaining_label.setText(f'{number(painted)} / {number(total)}')
        self.palette.update()

    def set_progress_mode(self, mode):
        self.settings['progress_mode'] = mode
        self.refresh()

    def stroke_done(self):
        self.refresh()
        if self.session.painting.progress == 1 and not self.completed_announced:
            self.completed_announced = True
            self.save_requested.emit()
            if self.settings.get("sound", False):
                QApplication.beep()
            QTimer.singleShot(0, self.show_completion)

    def show_completion(self):
        QMessageBox.information(
            self,
            tr("Bir resim, binlerce küçük an."),
            tr('Tebrikler! {title} tamamlandı.\n\n{cells} hücreye renk verdiniz.\n'
               'İlerlemeniz kaydediliyor. Yeni bir resim için koleksiyona dönebilirsiniz.',
               title=painting_title(self.session.painting.id, self.session.painting.title), cells=number(self.session.painting.target_map.size)),
        )

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
        if window is not self and hasattr(window, "sidebar"):
            self.hidden_panels.extend([window.sidebar, window.statusBar()])
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
