import json
import zipfile
from pathlib import Path

from pixel_coloring.importer.level_writer import read_level

ROOT = Path(__file__).parents[1]


def test_all_release_levels_start_unpainted():
    gallery = ROOT / 'src/pixel_coloring/resources/paintings'
    catalog = json.loads((gallery / 'catalog.json').read_text(encoding='utf-8'))
    for item in catalog:
        path = gallery / (item['id'] + '.pcolor')
        with zipfile.ZipFile(path) as archive:
            assert set(archive.namelist()) == {'metadata.json', 'palette.json', 'target.npy', 'preview.webp'}
        p = read_level(path)
        assert p.painted_count == 0 and not p.painted_mask.any()
