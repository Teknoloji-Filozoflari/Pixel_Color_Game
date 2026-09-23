import numpy as np
from PIL import Image, ImageDraw

from ..core.painting import Painting


def sample_paintings():
    """Original procedural pixel illustrations. No downloaded artwork."""
    for index, title, category in [
        (0, "Günbatımı Vadisi", "Doğa"),
        (1, "Meraklı Tilki", "Hayvanlar"),
        (2, "Gece Ekspresi", "Şehirler"),
        (3, "Ay Bahçesi", "Fantastik"),
        (4, "Küçük Dost", "Hayvanlar"),
        (5, "Sahil Feneri", "Doğa"),
    ]:
        im = Image.new("RGB", (64, 48), "#202B46")
        d = ImageDraw.Draw(im)
        if index in (0, 5):
            for y, color in [(0, "#475584"), (10, "#A87591"), (18, "#F0A780"), (28, "#F6C792")]:
                d.rectangle((0, y, 63, y + 12), fill=color)
            d.ellipse((42, 7, 54, 19), fill="#FFE3A3")
            d.polygon([(0, 31), (15, 15), (28, 30), (39, 20), (63, 36), (63, 47), (0, 47)], fill="#585B7E")
            d.polygon([(0, 39), (22, 28), (36, 38), (53, 29), (63, 34), (63, 47), (0, 47)], fill="#2E455D")
            d.polygon([(28, 36), (34, 36), (41, 47), (17, 47)], fill="#8AB6B1")
            for x, y in [(5, 34), (12, 31), (50, 34), (57, 32)]:
                d.rectangle((x, y, x + 1, y + 9), fill="#25394A")
                d.polygon([(x - 4, y + 5), (x, y - 4), (x + 4, y + 5)], fill="#25394A")
            if index == 5:
                d.rectangle((0, 34, 63, 47), fill="#387B92")
                for x in range(2, 64, 11):
                    d.line((x, 40, x + 6, 40), fill="#8AB6B1")
                d.polygon([(34, 44), (63, 35), (63, 47)], fill="#25394A")
                d.polygon([(47, 38), (49, 18), (55, 18), (57, 38)], fill="#F5DEB8")
                d.rectangle((49, 24, 55, 28), fill="#CB6559")
                d.rectangle((48, 15, 56, 19), fill="#FFE3A3")
                d.polygon([(46, 15), (52, 10), (58, 15)], fill="#CB6559")
        elif index in (1, 4):
            d.rectangle((0, 0, 63, 47), fill="#283F49")
            for x, y in [(5, 5), (50, 7), (12, 31), (54, 34), (3, 40)]:
                d.rectangle((x, y, x + 4, y + 2), fill="#44615B")
            d.ellipse((12, 38, 53, 44), fill="#1C303B")
            base, bright = ("#CC693B", "#F1A054") if index == 1 else ("#8C8FA8", "#B9B8C9")
            d.polygon(
                [(17, 27), (15, 8), (27, 17), (38, 17), (48, 8), (47, 30), (38, 39), (26, 39)], fill=base
            )
            d.polygon([(18, 12), (20, 23), (25, 18)], fill="#EDBFA0")
            d.polygon([(45, 12), (39, 18), (44, 23)], fill="#EDBFA0")
            d.rectangle((24, 20, 40, 32), fill=bright)
            d.polygon([(19, 27), (29, 29), (32, 34), (35, 29), (45, 27), (39, 38), (26, 38)], fill="#F4DFC0")
            d.rectangle((24, 25, 26, 27), fill="#202B36")
            d.rectangle((38, 25, 40, 27), fill="#202B36")
            d.rectangle((30, 32, 34, 34), fill="#202B36")
            if index == 4:
                d.line((14, 31, 25, 32), fill="#202B36")
                d.line((39, 32, 51, 31), fill="#202B36")
        elif index == 2:
            d.rectangle((0, 0, 63, 47), fill="#232944")
            d.ellipse((44, 5, 53, 14), fill="#F1DCAE")
            for x, y in [(5, 9), (22, 4), (33, 13), (59, 7)]:
                d.point((x, y), fill="#F1DCAE")
            for x, height in [(0, 20), (10, 30), (23, 23), (35, 27), (49, 19), (58, 28)]:
                d.rectangle((x, height, x + 8, 44), fill="#444C6D")
                for yy in range(height + 3, 40, 5):
                    for xx in range(x + 2, x + 7, 4):
                        d.rectangle((xx, yy, xx + 1, yy + 1), fill="#D9AB75")
            d.rectangle((0, 39, 63, 47), fill="#171F35")
            d.rectangle((6, 31, 51, 40), fill="#D57662")
            d.rectangle((9, 33, 48, 36), fill="#A9D9CF")
            for x in range(14, 49, 8):
                d.line((x, 32, x, 38), fill="#713F53")
            d.rectangle((5, 40, 54, 41), fill="#D9AB75")
            for x in (12, 42):
                d.rectangle((x, 41, x + 5, 43), fill="#444C6D")
        else:
            d.rectangle((0, 0, 63, 47), fill="#292B4B")
            d.ellipse((24, 3, 43, 22), fill="#F3DDB1")
            d.ellipse((31, 1, 46, 17), fill="#292B4B")
            for x, y in [(6, 5), (17, 11), (52, 8), (57, 22), (9, 23)]:
                d.line((x - 1, y, x + 1, y), fill="#D1A0C0")
                d.line((x, y - 1, x, y + 1), fill="#D1A0C0")
            d.rectangle((0, 41, 63, 47), fill="#365357")
            for x, y, size in [(8, 31, 8), (29, 30, 12), (48, 34, 8)]:
                d.rectangle((x + size // 2 - 1, y, x + size // 2 + 1, 44), fill="#E2BEA2")
                d.pieslice((x - 3, y - size, x + size + 3, y + 4), 180, 360, fill="#B97398")
                d.rectangle((x - 3, y - 1, x + size + 3, y + 1), fill="#D1A0C0")
                d.rectangle((x + 1, y - 6, x + 3, y - 4), fill="#F3DDB1")
        array = np.asarray(im)
        palette, target = np.unique(array.reshape(-1, 3), axis=0, return_inverse=True)
        enlarged = target.reshape(48, 64).repeat(2, axis=0).repeat(2, axis=1)
        yield Painting(f"sample-{index}-v1", title, palette, enlarged, category)


def ensure_samples(folder, database, progress=None):
    import json

    from .bundle_update import install_updated_sample
    from .library import remove_retired_samples

    remove_retired_samples(database, folder)
    # Detailed bundled paintings are installed without replacing progress or user files.
    import shutil
    from pathlib import Path

    import zipfile
    from types import SimpleNamespace

    gallery = Path(__file__).resolve().parents[1] / "resources/paintings"
    catalog = json.loads((gallery / "catalog.json").read_text(encoding="utf-8"))
    with database.connect() as con:
        con.execute("CREATE TABLE IF NOT EXISTS bundle_cache (id TEXT PRIMARY KEY, signature TEXT)")
        cache = dict(con.execute("SELECT id,signature FROM bundle_cache"))
        registered = {r[0]: r[1:] for r in con.execute(
            "SELECT id,width,height,palette_size,data_path FROM paintings")}
        saved = {r[0] for r in con.execute("SELECT painting_id FROM progress")}

    def signature(source, path, item):
        original, installed = source.stat(), path.stat()
        return json.dumps([str(source.resolve()), original.st_size, original.st_mtime_ns,
                           installed.st_size, installed.st_mtime_ns, item.get('revision', 1)])

    completed = []
    registrations = []
    total = len(catalog)
    for index, item in enumerate(catalog):
        source = gallery / (item['id'] + '.pcolor')
        path = folder / source.name
        expected = (item['width'], item['height'], item['colors'], str(path))
        unchanged = (path.exists() and registered.get(item['id']) == expected
                     and cache.get(item['id']) == signature(source, path, item))
        if unchanged:
            completed.append((item['id'], cache[item['id']]))
        elif item.get('revision', 1) > 1 and (path.exists() or item['id'] in saved or item['id'] in registered):
            install_updated_sample(source, path, database)
            completed.append((item['id'], signature(source, path, item)))
        else:
            if not path.exists():
                shutil.copy2(source, path)
            # Installing bundled art only needs its header, not millions of pixels.
            with zipfile.ZipFile(source) as archive:
                meta = json.loads(archive.read('metadata.json'))
                palette = json.loads(archive.read('palette.json'))
            painting = SimpleNamespace(**{key: meta.get(key, '') for key in
                                        ('id', 'title', 'author', 'category', 'width', 'height')},
                                       palette=palette)
            if (painting.id, painting.width, painting.height, len(palette)) != (
                    item['id'], item['width'], item['height'], item['colors']):
                raise ValueError('Koleksiyon bilgileri seviye dosyasıyla eşleşmiyor')
            registrations.append((painting, path))
            completed.append((item['id'], signature(source, path, item)))
        if progress:
            progress(index + 1, total)
    database.register_many(registrations)
    with database.connect() as con:
        con.executemany('INSERT OR REPLACE INTO bundle_cache VALUES (?,?)', completed)
