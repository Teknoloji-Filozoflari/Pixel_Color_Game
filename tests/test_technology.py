import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pixel_coloring.core.game_session import GameSession
from pixel_coloring.core.paint_engine import PaintingEngine, PaintResult
from pixel_coloring.importer.level_writer import read_level, read_thumbnail
from pixel_coloring.persistence.database import Database
from pixel_coloring.persistence.save_manager import SaveManager

RESOURCES = Path(__file__).parents[1] / 'src/pixel_coloring/resources'
GALLERY = RESOURCES / 'paintings'
CATALOG = {item['id']: item for item in json.loads((GALLERY / 'catalog.json').read_text(encoding='utf-8'))}
TECHNOLOGY = sorted((item for item in CATALOG.values() if item['category'] == 'Teknoloji'),
                    key=lambda item: item['order'])


def test_technology_sources_grids_progression_and_translations():
    assert len(TECHNOLOGY) == 91
    assert {item['id'] for item in TECHNOLOGY} == {f'sample-teknoloji-20260927-{i:03}' for i in range(1, 92)}
    assert Counter(item['tier'] for item in TECHNOLOGY) == Counter({tier: 13 for tier in range(1, 8)})
    assert [item['order'] for item in TECHNOLOGY] == list(range(1, 92))
    assert {item['source_order'] for item in TECHNOLOGY} == set(range(1, 92))
    titles = json.loads((RESOURCES / 'painting_titles.json').read_text(encoding='utf-8'))
    for item in TECHNOLOGY:
        reference = CATALOG[item['reference_id']]
        p = read_level(GALLERY / (item['id'] + '.pcolor'))
        assert p.category == 'Teknoloji' and p.title == item['title']
        assert p.meaning == ''
        assert (p.width, p.height) == (max(reference['width'], reference['height']),
                                       min(reference['width'], reference['height']))
        assert p.target_map.size == item['cells'] == reference['cells']
        assert item['colors'] == len(p.palette) <= item['color_budget'] == reference['colors']
        assert len(np.unique(p.target_map)) == len(p.palette)
        assert item['tier'] == reference['tier'] == (item['source_order'] - 1) // 13 + 1
        assert read_thumbnail(GALLERY / (p.id + '.pcolor'))
        assert set(titles[p.id]) == {'en', 'az', 'es', 'ru'} and all(titles[p.id].values())
    for tier in range(1, 8):
        group = [item for item in TECHNOLOGY if item['tier'] == tier]
        for key in ('cells', 'color_budget', 'complexity_score'):
            assert [item[key] for item in group] == sorted(item[key] for item in group)


@pytest.mark.parametrize('tier', range(1, 8))
def test_technology_paint_undo_save_reopen_and_export(tier, tmp_path):
    item = next(item for item in TECHNOLOGY if item['tier'] == tier)
    path = GALLERY / (item['id'] + '.pcolor')
    p = read_level(path)
    color = int(p.target_map[0, 0])
    engine = PaintingEngine(p)
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
    assert selected == color and np.array_equal(restored.painted_mask, p.painted_mask)
    output = tmp_path / 'image.png'
    Image.fromarray(restored.palette[restored.target_map]).save(output)
    with Image.open(output) as image:
        assert np.array_equal(np.asarray(image), p.palette[p.target_map])
