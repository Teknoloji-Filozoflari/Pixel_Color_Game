"""Install the bundled collection while preserving player progress and imports."""

import json
import shutil
import zipfile
from pathlib import Path
from types import SimpleNamespace

from .bundle_update import install_updated_sample
from .library import remove_retired_samples


def ensure_samples(folder, database, progress=None):
    remove_retired_samples(database, folder)
    # Detailed bundled paintings are installed without replacing progress or user files.
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
