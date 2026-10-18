import json
from pathlib import Path
from queue import SimpleQueue
from threading import Event

import numpy as np
import pytest
from PIL import Image

from pixel_coloring.core.game_session import GameSession
from pixel_coloring.core.painting import Painting
from pixel_coloring.core.timelapse import Timelapse, export_gif
from pixel_coloring.importer.batch import folder_images, import_batch
from pixel_coloring.importer.level_writer import read_level, write_level
from pixel_coloring.persistence.database import Database


def painting(id='new-feature'):
    return Painting(id, 'Test', np.array([[230, 20, 30], [20, 200, 40]]),
                    np.tile(np.arange(2), (8, 6)))


@pytest.fixture
def game(app):
    from pixel_coloring.ui.game import GameScreen

    screen = GameScreen(GameSession(painting()), {})
    screen.resize(960, 640)
    screen.show()
    app.processEvents()
    yield screen
    screen.dispose()
    screen.close()
    screen.deleteLater()


def test_appearance_controls_update_actual_canvas_and_sync_shortcuts(game, app):
    controls = game.appearance_menu.controls
    before = game.canvas.grab().toImage()
    controls['numbers'].setChecked(False)
    assert game.canvas.grab().toImage() != before
    controls['grid_width'].setValue(3)
    controls['number_scale'].setValue(150)
    assert game.settings['grid_width'] == 3
    assert game.settings['number_scale'] == 150
    game.toggle_grid()
    game.appearance_menu.sync()
    assert not controls['grid'].isChecked()
    game.appearance_menu.reset()
    assert game.grid_button.isChecked()
    assert controls['numbers'].isChecked()
    assert game.canvas.grab().toImage() == before


def test_new_toolbar_buttons_fit_small_window_without_overlap(game):
    widgets = [game.home_button, game.appearance_button, game.recording_button,
               game.info_button, game.fullscreen_button, game.pixel_count_label, game.progress_label]
    for index, widget in enumerate(widgets):
        assert game.status_header.rect().contains(widget.geometry())
        for other in widgets[index + 1:]:
            assert not widget.geometry().intersects(other.geometry())


def test_recording_is_opt_in_pause_resume_and_ui_signal_work(game, app):
    menu = game.recording_menu
    assert not menu.recorder.frames
    game.canvas.changed.emit()
    assert not menu.recorder.dirty
    menu.toggle_action.trigger()
    assert menu.timer.isActive()
    assert game.recording_button.isChecked()
    p = game.session.painting
    p.restore(p.target_map == 0)
    game.canvas.changed.emit()
    menu.recorder.capture()
    assert len(menu.recorder.frames) == 2
    menu.toggle_action.trigger()
    assert not menu.timer.isActive()
    assert not game.recording_button.isChecked()
    exports = []
    game.recording_export_requested.connect(lambda: exports.append(True))
    menu.export_action.trigger()
    assert exports == [True]


def test_timelapse_caps_memory_preserves_first_and_final_and_exports_real_animation(tmp_path):
    p = Painting('record', 'Record', np.array([[250, 10, 10]]), np.zeros((1, 400), dtype=np.uint8))
    recorder = Timelapse(p, limit=10)
    recorder.start()
    first = recorder.frames[0].copy()
    for x in range(p.width):
        p.painted_mask[0, x] = True
        recorder.changed()
        recorder.capture()
    recorder.pause()
    assert len(recorder.frames) <= 10
    assert np.array_equal(first, recorder.frames[0])
    assert (np.asarray(recorder.frames[-1]) == [250, 10, 10]).all()
    assert recorder.frames[-1].width <= 320
    path = export_gif(recorder.frames, tmp_path / 'record.gif')
    with Image.open(path) as gif:
        assert gif.n_frames > 1
        gif.seek(gif.n_frames - 1)
        assert (np.asarray(gif.convert('RGB')) == [250, 10, 10]).all()
        assert gif.info['duration'] >= 1200


def test_failed_gif_export_preserves_destination_and_cleans_temporary(tmp_path, monkeypatch):
    path = tmp_path / 'existing.gif'
    path.write_bytes(b'previous file')

    def fail(*args, **kwargs):
        raise OSError('disk full')

    monkeypatch.setattr(Image.Image, 'save', fail)
    with pytest.raises(OSError, match='disk full'):
        export_gif([Image.new('RGB', (2, 2))], path)
    assert path.read_bytes() == b'previous file'
    assert list(tmp_path.iterdir()) == [path]


def test_batch_preserves_aspect_ratio_skips_broken_files_and_keeps_sources(tmp_path):
    inputs = tmp_path / 'inputs'
    inputs.mkdir()
    for name, size in [('wide.PNG', (80, 40)), ('tall.jpg', (20, 60)), ('tiny.webp', (4, 3))]:
        Image.new('RGB', size, '#987654').save(inputs / name)
    (inputs / 'broken.png').write_bytes(b'broken image')
    (inputs / 'ignore.txt').write_text('not an image')
    original = painting()
    write_level(original, inputs / 'prepared.pcolor')
    dest = tmp_path / 'paintings'
    dest.mkdir()
    database = Database(tmp_path / 'batch.sqlite3')
    paths = folder_images(inputs)
    source_bytes = {p: p.read_bytes() for p in paths}
    result = import_batch(paths, (40, 30), 4, dest, database, Event(), SimpleQueue())
    assert len(result.imported) == 4
    assert len(result.errors) == 1
    assert result.errors[0][0] == 'broken.png'
    converted = {p.title: p for p in (read_level(path) for path in dest.iterdir())}
    assert (converted['wide'].width, converted['wide'].height) == (40, 20)
    assert (converted['tall'].width, converted['tall'].height) == (10, 30)
    assert (converted['tiny'].width, converted['tiny'].height) == (4, 3)
    assert converted['Test'].id != original.id
    assert np.array_equal(converted['Test'].palette, original.palette)
    assert all(p.read_bytes() == source_bytes[p] for p in paths)


def test_batch_cancels_between_files_preserving_already_added_work(tmp_path):
    paths = [tmp_path / (str(i) + '.png') for i in range(3)]
    for path in paths:
        Image.new('RGB', (4, 4)).save(path)
    stop = Event()

    class Progress:
        def put(self, value):
            stop.set()

    database = Database(tmp_path / 'cancel.sqlite3')
    result = import_batch(paths, (40, 30), None, tmp_path, database, stop, Progress())
    assert len(result.imported) == 1
    assert result.cancelled
    with database.connect() as con:
        assert con.execute('SELECT COUNT(*) FROM paintings').fetchone()[0] == 1


def test_batch_removes_orphan_when_database_registration_fails(tmp_path, monkeypatch):
    path = tmp_path / 'source.png'
    Image.new('RGB', (4, 4)).save(path)
    database = Database(tmp_path / 'failed.sqlite3')

    def fail(*args):
        raise OSError('database failure')

    monkeypatch.setattr(database, 'register', fail)
    result = import_batch([path], (10, 10), None, tmp_path, database, Event(), SimpleQueue())
    assert not result.imported
    assert result.errors == [('source.png', 'database failure')]
    assert not list(tmp_path.glob('*.pcolor'))


def test_completion_animation_stops_on_navigation_and_no_late_dialog(game, app, monkeypatch):
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QMessageBox

    from pixel_coloring.ui.completion import CompletionOverlay

    announced = []
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: announced.append(True))
    game.session.painting.restore(np.ones(game.session.painting.target_map.shape, dtype=bool))
    game.show_completion()
    overlay = game.canvas.findChildren(CompletionOverlay)[0]
    assert overlay.timer.isActive()
    game.dispose()
    assert not overlay.timer.isActive()
    overlay.started -= overlay.duration_ms / 1000 + 1
    overlay.tick()
    QTest.qWait(30)
    assert not announced
    assert not game.canvas.findChildren(CompletionOverlay)


def test_completion_without_animation_shows_same_actions_and_never_opens_dialog(game, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from pixel_coloring.ui.completion import CompletionOverlay

    game.settings['completion_animation'] = False
    game.session.painting.restore(np.ones(game.session.painting.target_map.shape, dtype=bool))
    announced = []
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: announced.append(True))
    game.show_completion()
    overlay = game.canvas.findChildren(CompletionOverlay)[0]
    assert overlay.awaiting_choice
    assert overlay.collection_button.isVisible()
    assert overlay.stay_button.isVisible()
    assert not overlay.timer.isActive()
    assert not announced


def test_completion_reveals_actions_in_same_card_once_without_second_popup(game, monkeypatch):
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QMessageBox

    from pixel_coloring.ui.completion import CompletionOverlay

    game.session.painting.restore(np.ones(game.session.painting.target_map.shape, dtype=bool))
    announced, finished = [], []
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: announced.append(True))
    game.show_completion()
    overlay = game.canvas.findChildren(CompletionOverlay)[0]
    overlay.finished.connect(lambda: finished.append(True))
    assert overlay.actions.isHidden()
    overlay.started -= 1.5
    overlay.tick()
    QTest.qWait(30)
    assert overlay.actions.isHidden()
    overlay.started -= overlay.duration_ms / 1000
    overlay.tick()
    overlay.tick()
    QTest.qWait(30)
    assert overlay.awaiting_choice
    assert overlay.actions.isVisible()
    assert not overlay.timer.isActive()
    assert finished == [True]
    assert not announced
    assert game.canvas.findChildren(CompletionOverlay) == [overlay]
    # A repeated completion callback must not add a second card.
    game.show_completion()
    assert game.canvas.findChildren(CompletionOverlay) == [overlay]


def test_hiding_game_cancels_completion_without_a_late_popup(game, monkeypatch):
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QMessageBox

    from pixel_coloring.ui.completion import CompletionOverlay

    game.session.painting.restore(np.ones(game.session.painting.target_map.shape, dtype=bool))
    announced = []
    monkeypatch.setattr(QMessageBox, 'information', lambda *args: announced.append(True))
    game.show_completion()
    overlay = game.canvas.findChildren(CompletionOverlay)[0]
    game.hide()
    assert overlay.ended
    assert not overlay.timer.isActive()
    overlay.started -= overlay.duration_ms / 1000 + 1
    overlay.tick()
    QTest.qWait(30)
    assert not announced


@pytest.mark.parametrize('choose_collection', [False, True])
def test_completion_choices_return_to_collection_or_keep_artwork(game, choose_collection):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest

    from pixel_coloring.ui.completion import CompletionOverlay

    p = game.session.painting
    p.restore(np.ones(p.target_map.shape, dtype=bool))
    game.settings['completion_animation'] = False
    returned = []
    game.back_requested.connect(lambda: returned.append(True))
    game.show_completion()
    overlay = game.canvas.findChildren(CompletionOverlay)[0]
    button = overlay.collection_button if choose_collection else overlay.stay_button
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    QTest.qWait(30)
    assert returned == ([True] if choose_collection else [])
    assert p.progress == 1
    if not choose_collection:
        assert not game.canvas.findChildren(CompletionOverlay)
        assert game.canvas.hasFocus()


@pytest.mark.parametrize('language', ['tr', 'en', 'az', 'es', 'ru'])
def test_completion_choices_fit_small_canvas_in_all_languages(game, app, language):
    from pixel_coloring.ui.completion import CompletionOverlay
    from pixel_coloring.ui.i18n import set_language

    game.session.painting.restore(np.ones(game.session.painting.target_map.shape, dtype=bool))
    game.settings['completion_animation'] = False
    set_language(language)
    try:
        game.show_completion()
        overlay = game.canvas.findChildren(CompletionOverlay)[0]
        # Exercise the smallest supported canvas as well as resize after animation.
        game.canvas.setFixedSize(320, 280)
        app.processEvents()
        assert overlay.geometry() == game.canvas.rect()
        assert overlay.rect().contains(overlay.actions.geometry())
        for button in (overlay.collection_button, overlay.stay_button):
            assert overlay.actions.rect().contains(button.geometry())
            assert button.width() >= button.sizeHint().width()
    finally:
        set_language('tr')


def test_celebration_follows_canvas_size_and_preserves_camera_and_progress(game, app):
    from PySide6.QtCore import Qt

    from pixel_coloring.ui.completion import CompletionOverlay

    p = game.session.painting
    p.restore(np.ones(p.target_map.shape, dtype=bool))
    game.canvas.camera.zoom = 40
    camera = game.canvas.camera.zoom, game.canvas.camera.pan_x, game.canvas.camera.pan_y
    mask = p.painted_mask.copy()
    game.show_completion()
    overlay = game.canvas.findChildren(CompletionOverlay)[0]
    overlay.started -= 1
    overlay.grab()
    assert overlay.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    assert game.canvas.childAt(game.canvas.rect().center()) is None
    assert (game.canvas.camera.zoom, game.canvas.camera.pan_x, game.canvas.camera.pan_y) == camera
    assert np.array_equal(p.painted_mask, mask)
    game.resize(1100, 760)
    app.processEvents()
    overlay.tick()
    assert overlay.geometry() == game.canvas.rect()


def test_info_card_has_factual_source_and_treats_user_metadata_as_plain_text(app):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLabel

    from pixel_coloring.ui.artwork_info import ArtworkInfoDialog

    p = painting('sample-harikalar-041')
    dialog = ArtworkInfoDialog(p)
    try:
        labels = dialog.findChildren(QLabel)
        assert any('Ayasofya' in label.text() for label in labels)
        links = [label for label in labels if label.openExternalLinks()]
        assert len(links) == 1
        assert 'https://whc.unesco.org/en/list/356/' in links[0].text()
    finally:
        dialog.close()
        dialog.deleteLater()
    p.id = 'user-upload'
    p.title = '<a href="https://example.invalid">Personal image</a>'
    p.meaning = '<img src="private-file">'
    dialog = ArtworkInfoDialog(p)
    try:
        assert not any(label.openExternalLinks() for label in dialog.findChildren(QLabel))
        for label in dialog.findChildren(QLabel):
            assert label.textFormat() == Qt.TextFormat.PlainText
    finally:
        dialog.close()
        dialog.deleteLater()


def test_curated_facts_cover_both_categories_and_keep_existing_translations():
    from pixel_coloring.ui.artwork_info import FACTS, RESOURCE
    from pixel_coloring.ui.i18n import TRANSLATIONS

    catalog = json.loads((RESOURCE.parent / 'paintings/catalog.json').read_text())
    ids = {entry['id'] for entry in catalog if entry['category'] in ('TÜRKİYE', 'Harikalar')}
    aliases = [id for fact in FACTS for id in fact['paintings']]
    assert len(aliases) == len(set(aliases))
    assert set(aliases) == ids
    for fact in FACTS:
        assert fact['language'] == 'tr'
        assert fact['source'].startswith('https://')
        assert fact['place'] and fact['source_name']
        assert 150 <= len(fact['text']) <= 650
        assert fact['text'].count('.') >= 3
        if fact['text'] in TRANSLATIONS:
            assert set(TRANSLATIONS[fact['text']]) == {'en', 'az', 'es', 'ru'}
    # Preserve all previously supported foreign-language landmark descriptions,
    # including the three city cards whose old descriptions named the wrong place.
    by_id = {id: fact for fact in FACTS for id in fact['paintings']}
    old_ids = [f'sample-harikalar-{n:03}' for n in [10, 19, 20, 27, 29, 30, 40, 41, 42, 43, 51, 52, 76]]
    old_ids += [f'sample-turkiye-{city}-01-v1' for city in
                ['istanbul', 'nevsehir', 'denizli', 'adiyaman', 'edirne', 'izmir', 'sanliurfa']]
    for id in old_ids:
        assert set(TRANSLATIONS[by_id[id]['text']]) == {'en', 'az', 'es', 'ru'}


def test_main_window_batch_gif_and_settings_persistence(app, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QDialog, QFileDialog

    from pixel_coloring.ui.batch_import import BatchImportDialog
    from pixel_coloring.ui.main_window import MainWindow

    (tmp_path / 'paintings').mkdir()
    source = tmp_path / 'source.png'
    Image.new('RGB', (8, 4), '#e03040').save(source)
    database = Database(tmp_path / 'window.sqlite3')
    monkeypatch.setattr(BatchImportDialog, 'exec', lambda self: QDialog.DialogCode.Accepted)
    window = MainWindow(tmp_path, database)
    try:
        window.begin_batch([source])
        result = window.job.result(timeout=5)
        window.poll()
        assert not window.job
        assert window.batch_dialog is None
        id = result.imported[0]
        assert id in window.metadata
        p = read_level(window.paths[id])
        window.show_game((p, 0, None))
        window.show()
        app.processEvents()
        window.game.appearance_menu.controls['grid_width'].setValue(4)
        window.game.recording_menu.toggle()
        p.restore(np.ones(p.target_map.shape, dtype=bool))
        window.game.canvas.changed.emit()
        monkeypatch.setattr(QFileDialog, 'getSaveFileName', lambda *args: (str(tmp_path / 'test.gif'), ''))
        window.export_recording()
        assert window.job_kind == 'gif'
        path = window.job.result(timeout=5)
        window.poll()
        assert window.game is not None
        assert Path(path).is_file()
    finally:
        window.close()
        window.deleteLater()
    assert database.get_settings()['grid_width'] == 4
