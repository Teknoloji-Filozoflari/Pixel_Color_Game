"""Install Cars using the same verified grid progression as Wonders."""
import argparse
import csv
import hashlib
import json
import os
import runpy
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from pixel_coloring.importer.level_writer import read_level, write_level

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / 'src/pixel_coloring/resources/paintings'
HELPERS = runpy.run_path(str(ROOT / 'packaging/import_wonders.py'))
convert = HELPERS['convert']
progression_plan = HELPERS['progression_plan']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    items = json.loads((args.source / '91-gorsel-envanteri.json').read_text(encoding='utf-8'))
    with (args.source / 'envanter.csv').open(encoding='utf-8-sig', newline='') as stream:
        entries = list(csv.DictReader(stream))
    verified = {entry['id']: entry for entry in entries}
    assert len(items) == len(entries) == len(verified) == len({item['id'] for item in items}) == 91
    assert Counter(item['tier'] for item in items) == Counter({tier: 13 for tier in range(1, 8)})
    assert {item['order'] for item in items} == set(range(1, 92))
    source_paths = {}
    for item in items:
        assert item['category'] == 'Arabalar ve Ulaşım Araçları' and item['id'].startswith('sample-arabalar-')
        entry = verified[item['id']]
        assert item['title'] == entry['title'] and item['file'] == entry['file']
        source = args.source / item['file']
        assert source.resolve().is_relative_to(args.source.resolve())
        assert hashlib.sha256(source.read_bytes()).hexdigest() == entry['sha256'], source
        with Image.open(source) as image:
            assert image.size == (int(entry['source_width']), int(entry['source_height']))
            image.verify()
        source_paths[item['id']] = source
        item['category'] = 'Arabalar'
    catalog_path = GALLERY / 'catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    plan = progression_plan(items, catalog, source_paths)
    if args.preview:
        canvas = Image.new('RGB', (960, 7 * 270), '#20252B')
        draw = ImageDraw.Draw(canvas)
        for tier in range(1, 8):
            group = [item for item in plan if item['tier'] == tier]
            for column, item in enumerate([group[0], group[6], group[-1]]):
                p = convert(source_paths[item['id']], item)
                image = Image.fromarray(p.palette[p.target_map])
                image = ImageOps.contain(image, (320, 240), Image.Resampling.NEAREST)
                x, y = column * 320, (tier - 1) * 270
                canvas.paste(image, (x + (320 - image.width) // 2, y + (240 - image.height) // 2))
                draw.text((x + 8, y + 246), f"Tier {tier}: {p.width}x{p.height}, {len(p.palette)} colors")
        output = ROOT / 'work/cars-conversion-preview.png'
        output.parent.mkdir(exist_ok=True)
        canvas.save(output)
        print('Validated 91 PNGs. Preview:', output)
        return
    existing = {item['id']: item for item in catalog}
    baseline = {GALLERY / (item['id'] + '.pcolor'): hashlib.sha256(
        (GALLERY / (item['id'] + '.pcolor')).read_bytes()).hexdigest()
        for item in catalog if item['id'] not in verified}
    staged = ROOT / 'work/cars-levels'
    staged.mkdir(parents=True, exist_ok=True)
    additions, updates = [], []
    for item in plan:
        if item['id'] in existing:
            previous = existing[item['id']]
            assert previous['source_sha256'] == verified[item['id']]['sha256']
            assert (previous['width'], previous['height'], previous['color_budget'], previous['order']) == (
                item['width'], item['height'], item['colors'], item['order'])
            continue
        p = convert(source_paths[item['id']], item)
        path = GALLERY / (p.id + '.pcolor')
        assert not path.exists(), path
        output = staged / path.name
        write_level(p, output)
        restored = read_level(output)
        assert (restored.id, restored.title, restored.category) == (item['id'], item['title'], 'Arabalar')
        assert np.array_equal(restored.palette, p.palette) and np.array_equal(restored.target_map, p.target_map)
        updates.append((output, path))
        additions.append(dict(id=p.id, title=p.title, category=p.category, width=p.width, height=p.height,
                              colors=len(p.palette), cells=p.target_map.size, tier=item['tier'],
                              difficulty=item['difficulty'], order=item['order'], revision=1,
                              color_budget=item['colors'], source_order=item['source_order'],
                              source_revision=item.get('revision', 1), reference_id=item['reference_id'],
                              complexity_score=item['complexity_score'], reference_cells=item['reference_cells'],
                              conversion_policy='game-progression-v3', source_sha256=verified[item['id']]['sha256']))
    for output, path in updates:
        os.replace(output, path)
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in baseline.items())
    catalog.extend(additions)
    temp = catalog_path.with_suffix('.tmp')
    temp.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, catalog_path)
    (ROOT / 'work/cars-progression-plan.json').write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Validated 91 PNGs; added', len(additions), 'Cars levels. Total:', len(catalog))


if __name__ == '__main__':
    main()
