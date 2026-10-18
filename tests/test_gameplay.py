
import numpy as np
import pytest

from pixel_coloring.core.game_session import GameSession
from pixel_coloring.core.painting import Painting
from pixel_coloring.persistence.database import Database
from pixel_coloring.persistence.save_manager import SaveManager


@pytest.fixture
def games(app):
    from PySide6.QtCore import QEvent

    from pixel_coloring.ui.game import GameScreen

    opened = []

    def create(painting=None, selected=None):
        if painting is None:
            painting = Painting('gameplay', 'Test',
                                np.array([[240, 10, 10], [210, 20, 20], [10, 230, 10],
                                          [20, 200, 20], [10, 10, 240], [20, 20, 210]]),
                                np.tile(np.arange(6), (2, 1)))
        game = GameScreen(GameSession(painting, selected=selected), {})
        opened.append(game)
        game.resize(1000, 700)
        game.show()
        game.activateWindow()
        game.canvas.setFocus()
        app.processEvents()
        return game

    yield create
    for game in opened:
        game.close()
        game.deleteLater()
    app.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def cell_point(canvas, x, y):
    from PySide6.QtCore import QPoint

    sx, sy = canvas.camera.cell_to_screen(x + .5, y + .5)
    return QPoint(round(sx), round(sy))


def test_palette_is_stable_spread_out_and_does_not_change_artwork(games):
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    palette = np.repeat(np.arange(0, 240, 10)[:, None], 3, axis=1)
    painting = Painting('gradient', 'Test', palette, np.arange(len(palette))[None, :])
    original = painting.palette[painting.target_map].copy()
    game = games(painting)
    session = game.session
    assert sorted(session.palette_order) == list(range(len(palette)))
    assert session.palette_order == GameSession(painting).palette_order
    spread = palette[list(session.palette_order)]
    assert np.abs(np.diff(spread, axis=0)).mean() > np.abs(np.diff(palette, axis=0)).mean() * 3
    assert np.array_equal(painting.palette[painting.target_map], original)
    assert session.color_numbers[session.selected] == 1
    for slot, color in enumerate(session.palette_order):
        pos = QPoint(slot % 5 * 46 + 22, slot // 5 * 46 + 22)
        assert game.palette.index_at(pos) == color
        assert session.color_numbers[color] == slot + 1
    QTest.mouseClick(game.palette, Qt.MouseButton.LeftButton, pos=QPoint(68, 22))
    assert session.selected == session.palette_order[1]
    assert game.canvas.cache.selected == session.selected


@pytest.mark.parametrize('zoom', [.5, 1.25, 5.5, 16, 48])
@pytest.mark.parametrize('key,dx,dy', [('Left', -1, 0), ('Right', 1, 0), ('Up', 0, -1), ('Down', 0, 1)])
def test_arrow_key_moves_exactly_one_cell_at_each_zoom(games, zoom, key, dx, dy):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    painting = Painting('camera', 'Test', np.array([[10, 20, 30]]), np.zeros((2048, 2048), dtype=np.uint8))
    canvas = games(painting).canvas
    c = canvas.camera
    c.zoom = zoom
    left, top, _, _ = c.view_bounds()
    c.pan_x, c.pan_y = left - 20 * zoom, top - 20 * zoom
    canvas.constrain_camera()
    before = c.pan_x, c.pan_y
    QTest.keyClick(canvas, getattr(Qt.Key, 'Key_' + key))
    assert c.pan_x == pytest.approx(before[0] - dx * zoom)
    assert c.pan_y == pytest.approx(before[1] - dy * zoom)


@pytest.mark.parametrize('fill', [False, True])
def test_completion_skips_finished_color_and_stops_current_drag(games, fill):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    game = games()
    session, canvas = game.session, game.canvas
    p = session.painting
    first, completed, following = session.palette_order[:3]
    mask = p.target_map == completed
    mask[1, first] = True
    p.restore(mask)
    game.select(first)
    game.set_fill_mode(fill)
    QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=cell_point(canvas, first, 0))
    assert p.counts[first] == p.totals[first]
    assert session.selected == following
    assert canvas.cache.selected == following
    assert not canvas.dragging
    assert canvas.last_cell is None
    count = p.painted_count
    QTest.mouseMove(canvas, cell_point(canvas, following, 0))
    QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=cell_point(canvas, following, 0))
    assert p.painted_count == count


def test_partial_color_does_not_advance_and_fit_ends_brush_stroke(games):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    game = games()
    canvas = game.canvas
    first = game.session.selected
    QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=cell_point(canvas, first, 0))
    assert game.session.selected == first
    assert canvas.dragging
    QTest.keyClick(canvas, Qt.Key.Key_F)
    assert not canvas.dragging
    count = game.session.painting.painted_count
    QTest.mouseMove(canvas, cell_point(canvas, first, 1))
    QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=cell_point(canvas, first, 1))
    assert game.session.painting.painted_count == count


def test_palette_and_canvas_show_matching_shuffled_numbers(games, monkeypatch):
    from PySide6.QtGui import QPainter

    from pixel_coloring.rendering import canvas as canvas_module

    game = games()
    labels = []

    class RecordingPainter(QPainter):
        def drawText(self, *args):
            labels.append(args[-1])
            return super().drawText(*args)

    monkeypatch.setattr(canvas_module, 'QPainter', RecordingPainter)
    game.canvas.grab()
    assert labels == [str(game.session.color_numbers[int(color)])
                      for color in game.session.painting.target_map.ravel()]


def test_resumed_color_is_visible_in_scrolled_palette(games):
    palette = np.arange(180).reshape(60, 3)
    painting = Painting('scroll', 'Test', palette, np.arange(60).reshape(6, 10))
    last = GameSession(painting).palette_order[-1]
    game = games(painting, selected=last)
    row_bottom = 12 * game.palette.cell
    scroll = game.palette_scroll
    assert scroll.verticalScrollBar().value() + scroll.viewport().height() >= row_bottom
    assert scroll.viewport().width() >= game.palette.width()


def test_last_color_wraps_to_earlier_unfinished_color(games):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    game = games()
    session = game.session
    first, last = session.palette_order[0], session.palette_order[-1]
    mask = session.painting.target_map != first
    mask[0, last] = False
    session.painting.restore(mask)
    game.select(last)
    QTest.mouseClick(game.canvas, Qt.MouseButton.LeftButton, pos=cell_point(game.canvas, last, 0))
    assert session.selected == first


def test_final_color_announces_and_saves_completion_once(games, app):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    game = games()
    p = game.session.painting
    color = game.session.selected
    mask = np.ones(p.target_map.shape, dtype=bool)
    mask[0, color] = False
    p.restore(mask)
    announced, saved = [], []
    game.show_completion = lambda: announced.append(True)
    game.save_requested.connect(lambda: saved.append(True))
    QTest.mouseClick(game.canvas, Qt.MouseButton.LeftButton, pos=cell_point(game.canvas, color, 0))
    app.processEvents()
    game.stroke_done()
    assert p.progress == 1
    assert game.session.selected == color
    assert announced == [True]
    assert saved == [True]


def test_saved_original_color_ids_and_masks_survive_display_shuffle(games, tmp_path):
    game = games()
    p = game.session.painting
    database = Database(tmp_path / 'progress.sqlite3')
    database.register(p, tmp_path / 'painting.pcolor')
    color = next(c for c in game.session.palette_order if game.session.color_numbers[c] != c + 1)
    game.select(color)
    game.session.engine.paint_cell(color, 0, color)
    saver = SaveManager(database)
    try:
        saver.save(game.session)
        saver.flush()
    finally:
        saver.close()
    restored = Painting(p.id, p.title, p.palette, p.target_map)
    _, selected = database.load(restored)
    assert selected == color
    assert np.array_equal(restored.painted_mask, p.painted_mask)
    resumed = GameSession(restored, selected=selected)
    assert resumed.palette_order == game.session.palette_order
    assert resumed.selected == color
    restored.restore(restored.target_map == color)
    resumed = GameSession(restored, selected=color)
    assert resumed.selected == resumed.next_unfinished_color(after=color)
    fresh = Painting('fresh', 'Test', p.palette, p.target_map)
    assert database.load(fresh) == (0, None)
    assert GameSession(fresh).color_numbers[GameSession(fresh).selected] == 1


@pytest.mark.parametrize('pos', [(-1, 22), (22, -1), (230, 22), (22, 92), (68, 68)])
def test_empty_palette_space_never_selects_a_color(games, pos):
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent

    game = games()
    selected = []
    game.palette.selected.connect(selected.append)
    point = QPointF(*pos)
    assert game.palette.index_at(point) is None
    event = QMouseEvent(QEvent.Type.MouseButtonPress, point, point,
                        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    game.palette.mousePressEvent(event)
    assert not selected


@pytest.mark.parametrize('fill', [False, True])
def test_wrong_color_does_not_paint_or_draw_an_overlay(games, fill):
    game = games()
    canvas = game.canvas
    wrong = next(c for c in range(6) if c != game.session.selected)
    point = cell_point(canvas, wrong, 0)
    before = canvas.grab().toImage()
    if fill:
        canvas.fill_at(point)
    else:
        canvas.paint_at(point)
    assert game.session.painting.painted_count == 0
    assert canvas.grab().toImage() == before


@pytest.mark.parametrize('language', ['tr', 'en', 'az', 'es', 'ru'])
@pytest.mark.parametrize('progress', [25.5, 100])
def test_collection_badge_uses_selected_language(app, monkeypatch, language, progress):
    from PySide6.QtGui import QPainter

    from pixel_coloring.ui import progress_tile
    from pixel_coloring.ui.i18n import percentage, set_language, tr

    labels = []

    class RecordingPainter(QPainter):
        def drawText(self, *args):
            labels.append(args[-1])
            return super().drawText(*args)

    set_language(language)
    tile = progress_tile.ProgressTile(progress)
    try:
        tile.resize(96, 92)
        tile.show()
        app.processEvents()
        monkeypatch.setattr(progress_tile, 'QPainter', RecordingPainter)
        tile.grab()
        assert labels == [tr('Bitti') if progress == 100 else percentage(progress)]
    finally:
        tile.close()
        set_language('tr')


def test_saved_view_restores_zoom_and_center_after_reopen(games, app, tmp_path):
    from pixel_coloring.ui.game import GameScreen

    p = Painting('view', 'View', np.array([[10, 20, 30]]), np.zeros((700, 900), dtype=np.uint8))
    game = games(p)
    c = game.canvas.camera
    c.zoom = 16
    game.canvas.constrain_camera()
    game.canvas.pan_cells(60, 40)
    saved_view = dict(game.session.view_state)
    database = Database(tmp_path / 'view.sqlite3')
    database.register(p, tmp_path / 'view.pcolor')
    saver = SaveManager(database)
    try:
        saver.save(game.session)
        saver.flush()
    finally:
        saver.close()
    restored = GameScreen(GameSession(p, view_state=database.load_view(p)), {})
    try:
        restored.resize(1100, 760)
        restored.show()
        app.processEvents()
        view = restored.session.view_state
        assert view['zoom'] == 16
        assert view['center_x'] == pytest.approx(saved_view['center_x'], abs=.5)
        assert view['center_y'] == pytest.approx(saved_view['center_y'], abs=.5)
    finally:
        restored.close()
        restored.deleteLater()
