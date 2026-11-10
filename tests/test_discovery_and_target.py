import json
from pathlib import Path

import numpy as np

from pixel_coloring.core.game_session import GameSession
from pixel_coloring.core.painting import Painting
from pixel_coloring.persistence.database import Database
from pixel_coloring.ui.i18n import LANGUAGES, TRANSLATIONS, set_language, tr

RESOURCES = Path(__file__).resolve().parents[1] / 'src/pixel_coloring/resources'


def painting():
    return Painting('demo', 'Demo', np.array([[20, 30, 40], [200, 40, 50]]),
                    np.array([[0, 1], [1, 0]], dtype=np.uint8), 'Doğa')


def test_languages_match_readme_and_every_string_is_complete():
    assert list(LANGUAGES) == ['tr', 'az', 'es', 'ru', 'en']
    for source, translations in TRANSLATIONS.items():
        assert set(translations) == {'en', 'az', 'es', 'ru'}, source
        for text in translations.values():
            assert text.strip(), source
    set_language('en')
    assert tr('Araçlar') == 'Vehicles'
    set_language('tr')
    assert tr('Araçlar') == 'Araçlar'


def test_catalog_uses_vehicles_category_not_cars():
    catalog = json.loads((RESOURCES / 'paintings/catalog.json').read_text(encoding='utf-8'))
    categories = {item['category'] for item in catalog}
    assert 'Araçlar' in categories
    assert 'Arabalar' not in categories
    assert sum(item['category'] == 'Araçlar' for item in catalog) == 91


def test_target_view_blocks_painting_and_shows_completed_image(app):
    from pixel_coloring.ui.game import GameScreen

    session = GameSession(painting())
    screen = GameScreen(session, {})
    screen.resize(960, 640)
    screen.show()
    app.processEvents()
    before = screen.canvas.grab().toImage()
    screen.toggle_target_view(True)
    assert screen.canvas.show_target
    assert not screen.palette.isEnabled()
    assert screen.canvas.grab().toImage() != before
    painted = session.painting.painted_count
    screen.canvas.paint_at(screen.canvas.rect().center())
    assert session.painting.painted_count == painted
    screen.toggle_target_view(False)
    assert screen.palette.isEnabled()
    screen.dispose()
    screen.close()
    screen.deleteLater()


def test_filter_menu_emits_changed_when_combo_selection_updates(app):
    from pixel_coloring.ui.collection_browser import FilterMenu

    menu = FilterMenu({
        'collection_difficulty': '',
        'collection_status': 'all',
        'collection_sort': 'catalog',
    })
    seen = []
    menu.changed.connect(lambda: seen.append(True))
    menu.status.setCurrentIndex(menu.status.findData('completed'))
    app.processEvents()
    assert seen
    assert menu.status.currentData() == 'completed'
    assert menu.is_active()
    menu.deleteLater()


def test_favorites_and_last_played_persist_for_collection_sorting(tmp_path):
    database = Database(tmp_path / 'progress.sqlite3')
    database.set_settings({'favorites': ['sample-arabalar-001'], 'collection_sort': 'recent'})
    assert database.get_settings()['favorites'] == ['sample-arabalar-001']
    p = painting()
    path = tmp_path / 'demo.pcolor'
    path.write_bytes(b'placeholder')
    database.register(p, path)
    from pixel_coloring.persistence.save_manager import SaveManager

    session = GameSession(p)
    session.selected = 0
    session.engine.paint_cell(0, 0, 0)
    saver = SaveManager(database)
    try:
        saver.save(session).result()
    finally:
        saver.close()
    progress = database.progress_map()
    assert progress[p.id][0] > 0
    assert progress[p.id][3] > 0
