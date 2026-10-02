"""Validate and bundle the supplied motif package without editing source PNGs."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from pixel_coloring.core.painting import Painting
from pixel_coloring.importer.level_writer import read_level, write_level

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / 'src/pixel_coloring/resources/paintings'


def convert(source, item, size=512, colors=12):
    with Image.open(source) as image:
        rgba = ImageOps.exif_transpose(image).convert('RGBA')
        rgb = Image.new('RGB', rgba.size, '#F4E8D0')
        rgb.paste(rgba, mask=rgba.getchannel('A'))
        rgb.thumbnail((size, size), Image.Resampling.LANCZOS)
        # Suppress tiny shade differences before reducing to a compact, undithered palette.
        quantized = ImageOps.posterize(rgb, 5).quantize(
            colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        raw = np.asarray(quantized)
        used, target = np.unique(raw, return_inverse=True)
        palette = np.asarray(quantized.getpalette(), dtype=np.uint8).reshape(-1, 3)[used]
        return Painting('sample-' + item['id'] + '-v1', item['name'], palette,
                        target.reshape(raw.shape), 'TÜRK MOTİFLERİ',
                        'Piksel Atölyesi', item['meaning'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    records = json.loads((args.source / 'manifest.json').read_text(encoding='utf-8'))
    assert len(records) == 91 and len({r['id'] for r in records}) == 91
    for item in records:
        assert item['status'] == 'generated', item['id']
        source = args.source / item['image']
        assert source.resolve().is_relative_to(args.source.resolve())
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256'], source
        with Image.open(source) as image:
            assert image.size == (item['width'], item['height']), source
            image.verify()
    if args.preview:
        canvas = Image.new('RGB', (3 * 320, 3 * 350), '#20252B')
        for row, item in enumerate([records[0], records[3], records[57]]):
            for col, (size, colors) in enumerate([(256, 8), (384, 12), (512, 12)]):
                p = convert(args.source / item['image'], item, size, colors)
                image = Image.fromarray(p.palette[p.target_map]).resize((320, 320))
                canvas.paste(image, (col * 320, row * 350))
        output = ROOT / 'work/motif-conversion-preview.png'
        output.parent.mkdir(exist_ok=True)
        canvas.save(output)
        print(output)
        return
    catalog = json.loads((GALLERY / 'catalog.json').read_text(encoding='utf-8'))
    original = [r for r in catalog if not r['id'].startswith('sample-turk-motif-')]
    assert len({item['id'] for item in original}) == len(original)
    for order, item in enumerate(records, 1):
        p = convert(args.source / item['image'], item)
        path = GALLERY / (p.id + '.pcolor')
        write_level(p, path)
        loaded = read_level(path)
        assert loaded.title == item['name'] and loaded.meaning == item['meaning']
        assert np.array_equal(loaded.target_map, p.target_map)
        assert np.array_equal(loaded.palette, p.palette)
        original.append(dict(id=p.id, title=p.title, category=p.category, meaning=p.meaning,
                             width=p.width, height=p.height, colors=len(p.palette),
                             cells=p.width*p.height, difficulty='Uzman', tier=7,
                             order=order, revision=1, source_id=item['id'],
                             source_sha256=item['sha256'], interpretation=item['interpretation']))
    (GALLERY / 'catalog.json').write_text(json.dumps(original, ensure_ascii=False, indent=2) + '\n',
                                         encoding='utf-8')
    print('Validated and installed 91 motifs; collection total:', len(original))


if __name__ == '__main__':
    main()
