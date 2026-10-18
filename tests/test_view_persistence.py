import numpy as np
import pytest

from pixel_coloring.core.game_session import GameSession
from pixel_coloring.core.painting import Painting
from pixel_coloring.persistence.database import Database
from pixel_coloring.persistence.save_manager import SaveManager


def test_database_without_view_table_remains_compatible(tmp_path):
    database = Database(tmp_path / 'legacy.sqlite3')
    p = Painting('legacy-view', 'Test', np.array([[10, 20, 30]]), np.zeros((2, 2), dtype=np.uint8))
    database.register(p, tmp_path / 'picture.pcolor')
    session = GameSession(p)
    session.engine.paint_cell(0, 0, 0)
    saver = SaveManager(database)
    saver.save(session)
    saver.close()
    with database.connect() as con:
        con.execute('DROP TABLE view_states')
    reopened = Database(database.path)
    restored = Painting(p.id, p.title, p.palette, p.target_map)
    reopened.load(restored)
    assert restored.painted_count == 1
    assert restored.painted_mask[0, 0]
    assert reopened.load_view(restored) is None
    with reopened.connect() as con:
        assert con.execute('PRAGMA user_version').fetchone()[0] == 1


@pytest.mark.parametrize('change', [dict(zoom=float('inf')), dict(zoom=-10), dict(zoom='invalid'), dict(width=99)])
def test_invalid_or_resized_view_is_ignored_without_losing_painting(tmp_path, change):
    database = Database(tmp_path / 'invalid.sqlite3')
    p = Painting('bad-view', 'Test', np.array([[10, 20, 30]]), np.zeros((2, 2), dtype=np.uint8))
    database.register(p, tmp_path / 'picture.pcolor')
    session = GameSession(p)
    session.engine.paint_cell(0, 0, 0)
    session.view_state = dict(zoom=16, center_x=1, center_y=1, width=2, height=2)
    session.view_state.update(change)
    saver = SaveManager(database)
    saver.save(session)
    saver.close()
    restored = Painting(p.id, p.title, p.palette, p.target_map)
    database.load(restored)
    assert restored.painted_count == 1
    assert database.load_view(restored) is None


def test_main_window_resumes_view_and_restart_clears_it(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from pixel_coloring.importer.level_writer import write_level
    from pixel_coloring.ui.main_window import MainWindow

    p = Painting('resume-window', 'Test', np.array([[10, 20, 30]]), np.zeros((500, 800), dtype=np.uint8))
    level = tmp_path / 'picture.pcolor'
    write_level(p, level)
    database = Database(tmp_path / 'resume-window.sqlite3')
    database.register(p, level)
    session = GameSession(p)
    session.engine.paint_cell(0, 0, 0)
    session.view_state = dict(zoom=16, center_x=320, center_y=200, width=800, height=500)
    saver = SaveManager(database)
    saver.save(session)
    saver.close()
    window = MainWindow(tmp_path, database)
    try:
        window.show()
        window.open_painting(p.id)
        window.job.result(timeout=5)
        window.poll()
        app.processEvents()
        state = window.game.session.view_state
        assert state['zoom'] == 16
        assert state['center_x'] == pytest.approx(320, abs=.5)
        assert state['center_y'] == pytest.approx(200, abs=.5)
        assert window.game.session.painting.painted_count == 1
        monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Yes)
        window.restart_painting(p.id)
        app.processEvents()
        assert window.game.session.painting.painted_count == 0
        assert database.load_view(p) is None
        assert window.game.canvas.camera.zoom != 16
    finally:
        window.close()
