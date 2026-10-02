"""Validate the Wonders source package and append its 91 bundled levels."""
import argparse
import csv
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from pixel_coloring.core.painting import Painting
from pixel_coloring.importer.level_writer import read_level, write_level

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / 'src/pixel_coloring/resources/paintings'
TARGETS = {1: (80, 60, 14), 2: (120, 90, 20), 3: (160, 120, 25),
           4: (200, 150, 28), 5: (280, 210, 35), 6: (400, 300, 40), 7: (800, 600, 52)}


def simplify_isolated_pixels(raw, passes):
    """Remove isolated specks only when five neighboring cells agree on a replacement."""
    result = raw.copy()
    for _ in range(passes):
        padded = np.pad(result, 1, mode='edge')
        neighbors = np.stack([padded[y:y + result.shape[0], x:x + result.shape[1]]
                              for y in range(3) for x in range(3) if (y, x) != (1, 1)])
        same = (neighbors == result).sum(axis=0)
        winner, votes = result.copy(), np.zeros(result.shape, dtype=np.uint8)
        for color in np.unique(result):
            count = (neighbors == color).sum(axis=0)
            better = count > votes
            winner[better], votes[better] = color, count[better]
        replace = (same <= 1) & (votes >= 5)
        result[replace] = winner[replace]
    return result


def convert(source, item):
    with Image.open(source) as image:
        rgba = ImageOps.exif_transpose(image).convert('RGBA')
        rgb = Image.new('RGB', rgba.size, '#FFFFFF')
        rgb.paste(rgba, mask=rgba.getchannel('A'))
        # BOX averages each pixel-art cluster without ringing or introducing dithering.
        width, height = item['width'], item['height']
        scale = min(width / rgb.width, height / rgb.height)
        fitted = rgb.resize((max(1, round(rgb.width * scale)), max(1, round(rgb.height * scale))),
                            Image.Resampling.BOX)
        # Fit the entire landmark; mirror the outer scenery rather than producing stretched stripes.
        left, top = (width - fitted.width) // 2, (height - fitted.height) // 2
        pixels = np.pad(np.asarray(fitted), ((top, height - fitted.height - top),
                        (left, width - fitted.width - left), (0, 0)), mode='reflect')
        rgb = Image.fromarray(pixels)
        quantized = rgb.quantize(colors=item['colors'], method=Image.Quantize.MEDIANCUT,
                                 dither=Image.Dither.NONE)
        raw = np.asarray(quantized)
        passes = {1: 2, 2: 1, 3: 1}.get(item['tier'], 0)
        if passes:
            raw = simplify_isolated_pixels(raw, passes)
        used, target = np.unique(raw, return_inverse=True)
        palette = np.asarray(quantized.getpalette(), dtype=np.uint8).reshape(-1, 3)[used]
        return Painting(item['id'], item['title'], palette, target.reshape(raw.shape), item.get('category', 'Harikalar'))


def progression_plan(items, catalog, source_paths):
    """Keep source tiers; increase cells/colors within each tier using the game's reference ranges."""
    reference = [item for item in catalog if item['category'] == 'Doğa']
    plan = []
    for tier in TARGETS:
        examples = sorted((item for item in reference if item.get('tier') == tier), key=lambda item: item['order'])
        minimum, maximum = min(item['cells'] for item in examples), max(item['cells'] for item in examples)
        # Nature, Animals and Fantasy share the same workload progression.
        for category in ('Hayvanlar', 'Fantastik'):
            others = sorted((item for item in catalog if item['category'] == category and item.get('tier') == tier),
                            key=lambda item: item['order'])
            assert [item['cells'] for item in examples] == [item['cells'] for item in others]
            assert all(abs(first['colors'] - second['colors']) <= 1
                       for first, second in zip(examples, others, strict=True))
        ranked = []
        for item in items:
            if item['tier'] != tier:
                continue
            probe = convert(source_paths[item['id']], dict(item, width=80, height=60, colors=12, tier=7))
            pixels = probe.target_map
            boundaries = float((pixels[:, 1:] != pixels[:, :-1]).mean()
                               + (pixels[1:] != pixels[:-1]).mean()) / 2
            specks = float((pixels != simplify_isolated_pixels(pixels, 1)).mean())
            ranked.append((boundaries + 2 * specks, item['order'], item))
        for index, (complexity, source_order, item) in enumerate(sorted(ranked)):
            fraction = index / max(1, len(ranked) - 1)
            example = examples[int(fraction * (len(examples) - 1) + .5)]
            width, height = max(example['width'], example['height']), min(example['width'], example['height'])
            colors = example['colors']
            plan.append(dict(item, width=width, height=height, colors=colors,
                             source_order=source_order, order=len(plan) + 1,
                             complexity_score=round(complexity, 6), reference_cells=[minimum, maximum],
                             reference_id=example['id']))
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--allow-missing', action='store_true', help='Import only available PNGs and report omissions')
    parser.add_argument('--replacement-metadata', type=Path, help='Verified metadata for the generated missing image')
    args = parser.parse_args()
    items = json.loads((args.source / '91-gorsel-envanteri.json').read_text(encoding='utf-8'))
    with (args.source / 'envanter.csv').open(encoding='utf-8-sig', newline='') as stream:
        entries = list(csv.DictReader(stream))
    assert len(items) == len(entries) == 91
    verified = {entry['id']: entry for entry in entries}
    assert len(verified) == len({item['id'] for item in items}) == 91
    assert Counter(item['tier'] for item in items) == Counter({tier: 13 for tier in TARGETS})
    assert {item['order'] for item in items} == set(range(1, 92))
    source_paths = {item['id']: args.source / item['file'] for item in items}
    replacement = None
    if args.replacement_metadata:
        replacement = json.loads(args.replacement_metadata.read_text(encoding='utf-8'))
        assert replacement['id'] == 'sample-harikalar-018'
        assert not source_paths[replacement['id']].exists(), 'Do not replace an existing original PNG'
        replacement_path = args.replacement_metadata.parent / replacement['file']
        assert replacement_path.resolve().is_relative_to(args.replacement_metadata.parent.resolve())
        source_paths[replacement['id']] = replacement_path
        verified[replacement['id']] = replacement
    missing = [item for item in items if not source_paths[item['id']].is_file()]
    if missing:
        print('Missing source images:', ', '.join(item['id'] for item in missing))
        if not args.allow_missing:
            raise FileNotFoundError('Source package is incomplete; use --allow-missing to import available files')
    items = [item for item in items if item not in missing]
    for item in items:
        entry = verified[item['id']]
        assert item['category'] == 'Harikalar' and item['id'].startswith('sample-harikalar-')
        assert (item['width'], item['height'], item['colors']) == TARGETS[item['tier']]
        assert entry['title'] == item['title']
        source = source_paths[item['id']]
        if entry is not replacement:
            assert entry['file'] == item['file']
            assert source.resolve().is_relative_to(args.source.resolve())
        assert hashlib.sha256(source.read_bytes()).hexdigest() == entry['sha256'], source
        with Image.open(source) as image:
            assert image.size == (int(entry['source_width']), int(entry['source_height']))
            assert abs(image.width / image.height - 4 / 3) < .005
            image.verify()
    catalog_path = GALLERY / 'catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    items = progression_plan(items, catalog, source_paths)
    if args.preview:
        canvas = Image.new('RGB', (960, 3 * 270), '#20252B')
        draw = ImageDraw.Draw(canvas)
        for index, item in enumerate(next(item for item in items if item['tier'] == tier) for tier in TARGETS):
            p = convert(source_paths[item['id']], item)
            preview = Image.fromarray(p.palette[p.target_map]).resize((320, 240), Image.Resampling.NEAREST)
            x, y = (index % 3) * 320, (index // 3) * 270
            canvas.paste(preview, (x, y))
            draw.text((x + 8, y + 246), f"Tier {item['tier']}: {p.width} x {p.height}, {len(p.palette)} colors")
        output = ROOT / 'work/wonders-conversion-preview.png'
        output.parent.mkdir(exist_ok=True)
        canvas.save(output)
        print(output)
        return
    existing = {item['id']: item for item in catalog}
    baseline = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in GALLERY.glob('*.pcolor')
                if path.stem not in verified}
    backup = ROOT / 'work/wonders-before-rebalance'
    staged = ROOT / 'work/wonders-rebalanced-levels'
    backup.mkdir(parents=True, exist_ok=True)
    staged.mkdir(parents=True, exist_ok=True)
    if not (backup / 'catalog.json').exists():
        shutil.copy2(catalog_path, backup / 'catalog.json')
    updates = []
    for item in items:
        if item['id'] in existing:
            assert existing[item['id']].get('source_sha256') == verified[item['id']]['sha256']
            if existing[item['id']].get('conversion_policy') == 'game-progression-v3':
                continue
        p = convert(source_paths[item['id']], item)
        path = GALLERY / (p.id + '.pcolor')
        if path.exists() and not (backup / path.name).exists():
            shutil.copy2(path, backup / path.name)
        output = staged / path.name
        write_level(p, output)
        restored = read_level(output)
        assert restored.id == item['id'] and restored.title == item['title']
        assert np.array_equal(p.target_map, restored.target_map)
        assert np.array_equal(p.palette, restored.palette)
        updates.append((output, path))
        existing[p.id] = dict(id=p.id, title=p.title, category=p.category, width=p.width, height=p.height,
                            colors=len(p.palette), cells=p.target_map.size, tier=item['tier'],
                            difficulty=item['difficulty'], order=item['order'], revision=3,
                            color_budget=item['colors'], source_order=item['source_order'],
                            reference_id=item['reference_id'],
                            complexity_score=item['complexity_score'], reference_cells=item['reference_cells'],
                            conversion_policy='game-progression-v3',
                            source_sha256=verified[item['id']]['sha256'],
                            source_generated=verified[item['id']] is replacement,
                            interpretation='Tanınan yapı ve doğal harikaların sanatsal AI yorumu.')
    for output, path in updates:
        os.replace(output, path)
    catalog = [existing[item['id']] for item in catalog if item['id'] not in source_paths] + [
        existing[item['id']] for item in items]
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in baseline.items())
    temp_catalog = catalog_path.with_suffix('.tmp')
    temp_catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp_catalog, catalog_path)
    report = ROOT / 'work/wonders-progression-plan.json'
    report.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Validated source PNGs:', len(items), '; missing:', len(missing), '; total paintings:', len(catalog))


if __name__ == '__main__':
    main()
