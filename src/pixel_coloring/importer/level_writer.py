import io
import json
import os
import zipfile

import numpy as np
from PIL import Image

from ..core.painting import Painting


def write_level(painting, path):
    metadata = dict(
        version=1,
        id=painting.id,
        title=painting.title,
        category=painting.category,
        author=painting.author,
        width=painting.width,
        height=painting.height,
    )
    target = io.BytesIO()
    np.save(target, painting.target_map, allow_pickle=False)
    preview = Image.fromarray(painting.palette[painting.target_map])
    preview.thumbnail(
        (320, 240), Image.Resampling.LANCZOS if max(preview.size) > 512 else Image.Resampling.NEAREST
    )
    thumb = io.BytesIO()
    preview.save(thumb, format="WEBP", lossless=True)
    temp = path.with_suffix(".tmp")
    try:
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False))
            z.writestr("palette.json", json.dumps(painting.palette.tolist()))
            z.writestr("target.npy", target.getvalue())
            z.writestr("preview.webp", thumb.getvalue())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_level(path):
    with zipfile.ZipFile(path) as z:
        limits = {
            "metadata.json": 16384,
            "palette.json": 2000000,
            "target.npy": 512 * 1024 * 1024,
            "preview.webp": 2000000,
        }
        for name, limit in limits.items():
            if z.getinfo(name).file_size > limit:
                raise ValueError("Seviye dosyası beklenen boyutu aşıyor")
        meta = json.loads(z.read("metadata.json"))
        if meta.get("version") != 1:
            raise ValueError("Desteklenmeyen seviye sürümü")
        target = np.load(io.BytesIO(z.read("target.npy")), allow_pickle=False)
        p = Painting(
            str(meta["id"]),
            str(meta["title"]),
            np.array(json.loads(z.read("palette.json"))),
            target,
            str(meta.get("category", "Diğer")),
            str(meta.get("author", "")),
        )
        if (p.width, p.height) != (meta["width"], meta["height"]):
            raise ValueError("Seviye boyutları tutarsız")
        return p


def read_thumbnail(path):
    with zipfile.ZipFile(path) as z:
        if z.getinfo("preview.webp").file_size > 2000000:
            raise ValueError("Önizleme çok büyük")
        return z.read("preview.webp")
