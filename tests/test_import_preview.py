import time
from concurrent.futures import Future

import numpy as np
import pytest
from PIL import Image

from pixel_coloring.importer.image_importer import import_image


@pytest.fixture
def source(tmp_path):
    pixels = np.random.default_rng(8).integers(0, 256, (60, 120, 3), dtype=np.uint8)
    path = tmp_path / 'original.png'
    Image.fromarray(pixels).save(path)
    return path


def wait_preview(app, dialog):
    deadline = time.monotonic() + 8
    while dialog.painting is None and time.monotonic() < deadline:
        app.processEvents()
        # qWait holds the GIL: a test can starve the Python conversion worker.
        # Process Qt events, then yield to the worker as the real event loop does.
        time.sleep(.01)
    job = dialog.job
    assert dialog.painting is not None, (
        f'{dialog.status.text()} (revision={dialog.revision}, job_revision={dialog.job_revision}, '
        f'job_done={job.done() if job is not None else None})'
    )


def test_preview_updates_size_colors_and_uses_exact_accepted_result(app, source):
    from pixel_coloring.ui.import_preview import ImportPreviewDialog

    original = source.read_bytes()
    dialog = ImportPreviewDialog(source)
    try:
        dialog.show()
        wait_preview(app, dialog)
        assert (dialog.painting.width, dialog.painting.height) == (120, 60)
        dialog.width_box.setValue(40)
        dialog.auto_colors_box.setChecked(False)
        dialog.colors_box.setValue(5)
        assert dialog.height_box.value() == 20
        assert dialog.painting is None
        wait_preview(app, dialog)
        result = dialog.painting
        assert (result.width, result.height) == (40, 20)
        assert len(result.palette) <= 5
        assert not dialog.original_preview.pixmap.isNull()
        assert not dialog.converted_preview.pixmap.isNull()
        dialog.accept()
        assert dialog.result() == dialog.DialogCode.Accepted
        assert dialog.painting is result
        assert source.read_bytes() == original
    finally:
        dialog.reject()


def test_stale_preview_cannot_be_accepted_and_cancel_writes_nothing(app, source, tmp_path):
    from pixel_coloring.ui.import_preview import ImportPreviewDialog, build_preview

    dialog = ImportPreviewDialog(source)
    files = set(tmp_path.iterdir())
    try:
        dialog.debounce.stop()
        old_revision = dialog.revision
        stale = build_preview(source, (120, 60), 4)
        dialog.width_box.setValue(30)
        dialog.debounce.stop()
        future = Future()
        future.set_result(stale)
        dialog.job, dialog.job_revision = future, old_revision
        dialog.poll_preview()
        assert dialog.painting is None
        dialog.accept()
        assert not dialog.closed
        wait_preview(app, dialog)
        assert dialog.painting.width == 30
        dialog.reject()
        assert dialog.closed and not dialog.poll_timer.isActive()
        assert set(tmp_path.iterdir()) == files
    finally:
        dialog.reject()


def test_preview_reports_conversion_failure_and_allows_retry(app, source):
    from pixel_coloring.ui.import_preview import ImportPreviewDialog

    dialog = ImportPreviewDialog(source)
    try:
        dialog.debounce.stop()
        future = Future()
        future.set_exception(OSError('source unavailable'))
        dialog.job, dialog.job_revision = future, dialog.revision
        dialog.poll_preview()
        assert 'source unavailable' in dialog.status.text()
        assert dialog.painting is None
        dialog.width_box.setValue(80)
        wait_preview(app, dialog)
        assert dialog.painting.width == 80
    finally:
        dialog.reject()


def test_large_source_can_be_resized_before_import_and_exif_is_applied(tmp_path):
    source = tmp_path / 'wide.jpg'
    image = Image.new('RGB', (2400, 1200), '#12ab34')
    exif = Image.Exif()
    exif[274] = 6
    image.save(source, exif=exif)
    with pytest.raises(ValueError, match='1920'):
        import_image(source)
    painting = import_image(source, colors=4, size=(300, 600))
    assert (painting.width, painting.height) == (300, 600)
    assert len(painting.palette) == 1


def test_transparency_stays_white_after_resizing(tmp_path):
    source = tmp_path / 'transparent.png'
    Image.new('RGBA', (20, 10), (255, 0, 0, 0)).save(source)
    painting = import_image(source, colors=2, size=(10, 5))
    assert painting.palette.tolist() == [[255, 255, 255]]


def test_preview_caps_large_sources_to_game_limits(app, tmp_path):
    from pixel_coloring.ui.import_preview import ImportPreviewDialog

    source = tmp_path / 'large.png'
    Image.new('RGB', (2400, 1600), '#abcdef').save(source)
    dialog = ImportPreviewDialog(source)
    try:
        wait_preview(app, dialog)
        assert dialog.width_box.value() <= 1920
        assert dialog.height_box.value() <= 1080
        assert dialog.painting.width / dialog.painting.height == pytest.approx(1.5)
    finally:
        dialog.reject()


@pytest.mark.parametrize('accept', [False, True])
def test_main_window_imports_only_accepted_preview_result(app, source, tmp_path, monkeypatch, accept):
    from PySide6.QtWidgets import QDialog, QFileDialog

    from pixel_coloring.importer.level_writer import read_level
    from pixel_coloring.persistence.database import Database
    from pixel_coloring.ui import import_preview
    from pixel_coloring.ui.main_window import MainWindow

    prepared = import_image(source, colors=4, size=(40, 20))

    class Preview:
        def __init__(self, *args):
            self.painting = prepared

        def exec(self):
            return QDialog.DialogCode.Accepted if accept else QDialog.DialogCode.Rejected

        def deleteLater(self):
            pass

    monkeypatch.setattr(import_preview, 'ImportPreviewDialog', Preview)
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *args: (str(source), ''))
    (tmp_path / 'paintings').mkdir()
    database = Database(tmp_path / 'import.sqlite3')
    window = MainWindow(tmp_path, database)
    try:
        window.import_dialog()
        if accept:
            assert window.job.result(timeout=5) == prepared.id
            window.poll()
            saved = read_level(tmp_path / 'paintings' / (prepared.id + '.pcolor'))
            assert np.array_equal(saved.target_map, prepared.target_map)
            assert np.array_equal(saved.palette, prepared.palette)
            assert (saved.width, saved.height) == (40, 20)
            assert prepared.id in window.metadata
        else:
            assert window.job is None
            assert not list((tmp_path / 'paintings').iterdir())
            assert not window.metadata
    finally:
        window.close()
