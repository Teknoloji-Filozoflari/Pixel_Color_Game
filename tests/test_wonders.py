import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pixel_coloring.core.game_session import GameSession
from pixel_coloring.core.paint_engine import PaintingEngine, PaintResult
from pixel_coloring.core.painting import Painting
from pixel_coloring.importer.level_writer import read_level, read_thumbnail, write_level
from pixel_coloring.persistence.database import Database
from pixel_coloring.persistence.save_manager import SaveManager
from pixel_coloring.services.bundle_update import install_updated_sample

ROOT = Path(__file__).parents[1]
RESOURCES = ROOT / 'src/pixel_coloring/resources'
GALLERY = RESOURCES / 'paintings'
WONDERS = [item for item in json.loads((GALLERY / 'catalog.json').read_text(encoding='utf-8'))
           if item['category'] == 'Harikalar']
CATALOG = {item['id']: item for item in json.loads((GALLERY / 'catalog.json').read_text(encoding='utf-8'))}


def test_wonders_pixels_titles_tiers_and_generated_source():
    assert len(WONDERS) == 91
    assert {item['id'] for item in WONDERS} == {f'sample-harikalar-{i:03}' for i in range(1, 92)}
    assert Counter(item['tier'] for item in WONDERS) == Counter({tier: 13 for tier in range(1, 8)})
    assert [item['order'] for item in WONDERS] == list(range(1, 92))
    titles = json.loads((RESOURCES / 'painting_titles.json').read_text(encoding='utf-8'))
    for item in WONDERS:
        p = read_level(GALLERY / (item['id'] + '.pcolor'))
        reference = CATALOG[item['reference_id']]
        width, height = max(reference['width'], reference['height']), min(reference['width'], reference['height'])
        limit = reference['colors']
        assert (p.width, p.height) == (width, height)
        assert item['colors'] == len(p.palette) <= limit
        assert item['color_budget'] == limit and item['cells'] == reference['cells']
        assert item['tier'] == reference['tier'] and item['revision'] == 3
        assert item['tier'] == (item['source_order'] - 1) // 13 + 1
        assert len(np.unique(p.target_map)) == len(p.palette)
        assert p.target_map.size == item['cells']
        assert p.title == item['title'] and p.category == 'Harikalar'
        assert p.meaning == ''
        assert set(titles[p.id]) == {'en', 'az', 'es', 'ru'}
        assert all(titles[p.id].values())
        assert read_thumbnail(GALLERY / (p.id + '.pcolor'))
    generated = next(item for item in WONDERS if item['source_generated'])
    assert generated['id'] == 'sample-harikalar-018'
    source_metadata = ROOT / 'packaging/sources/harikalar/018-generation.json'
    source = json.loads(source_metadata.read_text(encoding='utf-8'))
    digest = hashlib.sha256((source_metadata.parent / source['file']).read_bytes()).hexdigest()
    assert digest == source['sha256'] == generated['source_sha256']
    for tier in range(1, 8):
        group = [item for item in WONDERS if item['tier'] == tier]
        for key in ('cells', 'color_budget', 'complexity_score'):
            assert [item[key] for item in group] == sorted(item[key] for item in group)


@pytest.mark.parametrize('tier', range(1, 8))
def test_wonders_paint_undo_save_reopen_and_export(tier, tmp_path):
    item = next(item for item in WONDERS if item['tier'] == tier)
    path = GALLERY / (item['id'] + '.pcolor')
    p = read_level(path)
    engine = PaintingEngine(p)
    color = int(p.target_map[0, 0])
    assert engine.paint_cell(0, 0, color) is PaintResult.CORRECT
    engine.end_stroke()
    assert len(engine.undo()) == 1 and p.painted_count == 0
    assert len(engine.redo()) == 1 and p.painted_count == 1
    session = GameSession(p)
    session.selected = color
    database = Database(tmp_path / 'progress.sqlite3')
    database.register(p, path)
    saver = SaveManager(database)
    try:
        saver.save(session).result()
    finally:
        saver.close()
    restored = read_level(path)
    _, selected = database.load(restored)
    assert np.array_equal(restored.painted_mask, p.painted_mask)
    assert selected == color
    output = tmp_path / 'image.png'
    Image.fromarray(restored.palette[restored.target_map]).save(output)
    with Image.open(output) as image:
        assert np.array_equal(np.asarray(image), p.palette[p.target_map])


@pytest.mark.parametrize('tier', range(1, 8))
@pytest.mark.parametrize('complete', [False, True])
def test_rebalanced_wonders_migrate_old_progress_with_exact_backup(tier, complete, tmp_path):
    item = next(item for item in WONDERS if item['tier'] == tier)
    source = GALLERY / (item['id'] + '.pcolor')
    installed = tmp_path / source.name
    palette = np.array([[220, 10, 10], [15, 210, 15]], dtype=np.uint8)
    old = Painting(item['id'], item['title'], palette, np.zeros((60, 80), dtype=np.uint8), 'Harikalar')
    mask = np.ones((60, 80), dtype=bool) if complete else np.indices((60, 80))[1] < 20
    old.restore(mask)
    write_level(old, installed)
    original = installed.read_bytes()
    database = Database(tmp_path / 'migration.sqlite3')
    database.register(old, installed)
    session = GameSession(old)
    session.selected = 1
    saver = SaveManager(database)
    try:
        saver.save(session).result()
    finally:
        saver.close()
    install_updated_sample(source, installed, database)
    restored = read_level(installed)
    _, selected = database.load(restored)
    expected = np.asarray(Image.fromarray(mask.astype(np.uint8)).resize(
        (restored.width, restored.height), Image.Resampling.NEAREST), dtype=bool)
    assert np.array_equal(restored.painted_mask, expected)
    assert restored.painted_count == int(expected.sum())
    if complete:
        assert restored.progress == 1
    closest = int(np.argmin(((restored.palette.astype(np.int32) - palette[1].astype(np.int32)) ** 2).sum(axis=1)))
    assert selected == closest
    backup = tmp_path / 'backups' / (old.id + '-' + hashlib.sha256(original).hexdigest()[:16])
    assert (backup / installed.name).read_bytes() == original
    assert json.loads((backup / 'progress.json').read_text(encoding='utf-8'))['progress'] is not None
    install_updated_sample(source, installed, database)
    again = read_level(installed)
    database.load(again)
    assert np.array_equal(again.painted_mask, expected)


def test_easy_cleanup_removes_specks_without_erasing_thin_lines():
    import runpy

    simplify = runpy.run_path(str(ROOT / 'packaging/import_wonders.py'))['simplify_isolated_pixels']
    pixels = np.zeros((7, 7), dtype=np.uint8)
    pixels[1, 1] = 1
    pixels[3, 1:6] = 1
    result = simplify(pixels, 1)
    assert result[1, 1] == 0
    assert np.all(result[3, 2:5] == 1)
    assert set(np.unique(result)) <= set(np.unique(pixels))
