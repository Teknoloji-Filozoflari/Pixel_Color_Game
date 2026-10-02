import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pixel_coloring.core.game_session import GameSession
from pixel_coloring.core.paint_engine import PaintResult
from pixel_coloring.core.painting import Painting
from pixel_coloring.importer.level_writer import read_level, write_level
from pixel_coloring.persistence.database import Database
from pixel_coloring.persistence.save_manager import SaveManager
from pixel_coloring.services.samples import ensure_samples

RESOURCES = Path(__file__).parents[1] / 'src/pixel_coloring/resources'
GALLERY = RESOURCES / 'paintings'
MOTIFS = [item for item in json.loads((GALLERY / 'catalog.json').read_text(encoding='utf-8'))
          if item['category'] == 'TÜRK MOTİFLERİ']


def test_all_motifs_have_valid_pixels_and_metadata():
    assert len(MOTIFS) == len({item['source_id'] for item in MOTIFS}) == 91
    for item in MOTIFS:
        p = read_level(GALLERY / (item['id'] + '.pcolor'))
        assert p.id == 'sample-' + item['source_id'] + '-v1'
        assert p.title == item['title'] and p.meaning == item['meaning']
        assert p.category == 'TÜRK MOTİFLERİ'
        assert p.width <= 1920 and p.height <= 1080
        assert p.target_map.size == item['cells'] <= 2073600
        assert len(p.palette) == item['colors'] <= 12
        assert len(np.unique(p.target_map)) == len(p.palette)
    assert {'Koç', 'Koçboynuzu'} <= {item['title'] for item in MOTIFS}


def test_meaning_roundtrip_and_legacy_compatibility(tmp_path):
    p = read_level(GALLERY / (MOTIFS[0]['id'] + '.pcolor'))
    path = tmp_path / 'motif.pcolor'
    write_level(p, path)
    assert read_level(path).meaning == p.meaning
    legacy = io.BytesIO()
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(legacy, 'w') as target:
        for name in source.namelist():
            content = source.read(name)
            if name == 'metadata.json':
                metadata = json.loads(content)
                metadata.pop('meaning')
                content = json.dumps(metadata).encode('utf-8')
            target.writestr(name, content)
    legacy.seek(0)
    assert read_level(legacy).meaning == ''


def test_bundle_install_preserves_saved_progress_and_exports(tmp_path):
    database = Database(tmp_path / 'progress.sqlite3')
    folder = tmp_path / 'paintings'
    folder.mkdir()
    old = Painting('existing-import', 'Original', np.array([[20, 30, 40]]), np.zeros((2, 2), dtype=int))
    database.register(old, folder / 'original.pcolor')
    session = GameSession(old)
    session.engine.paint_cell(0, 0, 0)
    saver = SaveManager(database)
    try:
        saver.save(session).result()
        ensure_samples(folder, database)
        reloaded = Painting(old.id, old.title, old.palette, old.target_map)
        database.load(reloaded)
        assert np.array_equal(reloaded.painted_mask, old.painted_mask)
        motif = read_level(folder / (MOTIFS[0]['id'] + '.pcolor'))
        session = GameSession(motif)
        color = int(motif.target_map[0, 0])
        assert session.engine.paint_cell(0, 0, color) is PaintResult.CORRECT
        x, y = 1, 1
        color = int(motif.target_map[y, x])
        if motif.painted_mask[y, x]:
            x, y = 2, 2
            color = int(motif.target_map[y, x])
        result, indices = session.engine.fill_region(x, y, color)
        assert result is PaintResult.CORRECT and len(indices) > 0
        assert np.all(motif.target_map.ravel()[indices] == color)
        saver.save(session).result()
        ensure_samples(folder, database)
        restored = read_level(folder / (motif.id + '.pcolor'))
        database.load(restored)
        assert np.array_equal(restored.painted_mask, motif.painted_mask)
        image_path = tmp_path / 'completed.png'
        Image.fromarray(restored.palette[restored.target_map]).save(image_path)
        with Image.open(image_path) as image:
            assert image.size == (motif.width, motif.height)
    finally:
        saver.close()


@pytest.fixture(scope='module')
def app():
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtWidgets import QApplication

    from pixel_coloring.ui.theme import apply_theme
    application = QApplication.instance() or QApplication([])
    apply_theme(application)
    yield application


def test_five_languages_and_user_titles(app):
    from pixel_coloring.ui.i18n import LANGUAGES, painting_meaning, painting_title, set_language, tr
    try:
        for language in LANGUAGES:
            set_language(language)
            for item in MOTIFS:
                assert painting_title(item['id'], item['title'])
                assert painting_meaning(item['id'], item['meaning'])
                if language != 'tr':
                    titles = json.loads((RESOURCES / 'painting_titles.json').read_text(encoding='utf-8'))
                    meanings = json.loads((RESOURCES / 'painting_meanings.json').read_text(encoding='utf-8'))
                    assert language in titles[item['id']] and language in meanings[item['id']]
            assert tr('TÜRK MOTİFLERİ') != 'TÜRK MOTİFLERİ' or language == 'tr'
            assert painting_title('user-upload', 'My image') == 'My image'
    finally:
        set_language('tr')


def test_collection_and_game_meanings_at_minimum_window_size(app, tmp_path):
    from PySide6.QtWidgets import QLabel

    from pixel_coloring.ui.game import GameScreen
    from pixel_coloring.ui.i18n import painting_meaning, set_language
    from pixel_coloring.ui.main_window import MainWindow

    database = Database(tmp_path / 'ui.sqlite3')
    p = read_level(GALLERY / (MOTIFS[4]['id'] + '.pcolor'))
    database.register(p, GALLERY / (p.id + '.pcolor'))
    window = MainWindow(tmp_path, database)
    try:
        window.resize(960, 640)
        window.collection_category = 'TÜRK MOTİFLERİ'
        window.show()
        app.processEvents()
        assert list(window.category_buttons)[-6:] == ['TÜRKİYE', 'TÜRK MOTİFLERİ', 'Harikalar', 'Teknoloji', 'Arabalar', 'İçe aktarılan']
        for language in ['tr', 'az', 'en', 'es', 'ru']:
            if window.settings['language'] != language:
                window.change_language(language)
            app.processEvents()
            assert window.width() == 960
            meaning = window.stack.currentWidget().findChild(QLabel, 'paintingMeaning')
            assert meaning is not None and meaning.wordWrap()
            assert meaning.text() == painting_meaning(p.id, p.meaning)
            game = GameScreen(GameSession(p), window.settings)
            game.resize(960, 640)
            game.show()
            app.processEvents()
            line = game.findChild(QLabel, 'gamePaintingMeaning')
            assert line.text() == painting_meaning(p.id, p.meaning)
            assert line.wordWrap() and line.height() >= line.heightForWidth(line.width())
            game.close()
        empty = Painting('old', 'Legacy', p.palette, p.target_map)
        game = GameScreen(GameSession(empty), window.settings)
        assert game.findChild(QLabel, 'gamePaintingMeaning') is None
        game.close()
    finally:
        window.close()
        set_language('tr')


def test_pixel_count_selector_and_painted_percentage(app, tmp_path):
    from PySide6.QtWidgets import QLabel

    from pixel_coloring.ui.game import GameScreen
    from pixel_coloring.ui.i18n import percentage

    p = Painting('status-test', 'Status', np.array([[10, 20, 30], [40, 50, 60]]),
                 np.array([[0, 0], [1, 1]]))
    session = GameSession(p)
    session.engine.paint_cell(0, 0, 0)
    session.engine.paint_cell(0, 1, 1)
    settings = {'progress_mode': 'remaining'}
    game = GameScreen(session, settings)
    try:
        assert isinstance(game.progress_label, QLabel)
        assert game.progress_label.text() == percentage(50)
        assert game.pixel_count_label.text() == '1 / 2'
        assert len(game.pixel_count_label.menu().actions()) == 2
        game.pixel_count_actions['image'].trigger()
        assert game.pixel_count_label.text() == '2 / 4'
        assert game.pixel_count_actions['image'].isChecked()
        session.engine.paint_cell(1, 0, 0)
        game.refresh()
        assert game.pixel_count_label.text() == '3 / 4'
        assert game.progress_label.text() == percentage(75)
        game.pixel_count_actions['selected'].trigger()
        assert game.pixel_count_label.text() == '2 / 2'
        game.select(1)
        assert game.pixel_count_label.text() == '1 / 2'
        game.set_pixel_count_mode('image')
        database = Database(tmp_path / 'counter-settings.sqlite3')
        database.set_settings(settings)
        reopened = GameScreen(session, database.get_settings())
        try:
            assert reopened.pixel_count_actions['image'].isChecked()
            assert reopened.pixel_count_label.text() == '3 / 4'
            assert reopened.progress_label.text() == percentage(75)
        finally:
            reopened.close()
    finally:
        game.close()


@pytest.mark.parametrize('category', ['Harikalar', 'Teknoloji', 'Arabalar'])
def test_filter_translations_and_category_wrapping(app, tmp_path, category):
    from pixel_coloring.ui.i18n import set_language, tr
    from pixel_coloring.ui.main_window import MainWindow
    from pixel_coloring.ui.progress_tile import ProgressTile

    catalog = json.loads((GALLERY / 'catalog.json').read_text(encoding='utf-8'))
    database = Database(tmp_path / 'wonders-ui.sqlite3')
    entries = [(read_level(GALLERY / (item['id'] + '.pcolor')), GALLERY / (item['id'] + '.pcolor'))
               for item in catalog if item['category'] == category]
    database.register_many(entries)
    database.register(entries[0][0], entries[0][1])
    old = read_level(GALLERY / (MOTIFS[0]['id'] + '.pcolor'))
    database.register(old, GALLERY / (old.id + '.pcolor'))
    window = MainWindow(tmp_path, database)
    try:
        window.collection_category = category
        window.show_collection()
        window.resize(960, 640)
        window.show()
        for language in ['tr', 'az', 'en', 'es', 'ru']:
            if language != window.settings['language']:
                window.change_language(language)
            app.processEvents()
            assert window.width() == 960
            assert window.collection_category == category
            assert window.category_buttons[category].text() == tr(category)
            tiles = window.stack.currentWidget().findChildren(ProgressTile)
            visible = [tile for tile in tiles if not tile.isHidden()]
            assert len(visible) == 91
            assert all(tile.property('level_category') == category for tile in visible)
            assert [tile.property('level_order') for tile in visible] == list(range(1, 92))
            for tab in window.category_buttons.values():
                assert tab.geometry().right() < tab.parentWidget().width()
    finally:
        window.close()
        set_language('tr')
