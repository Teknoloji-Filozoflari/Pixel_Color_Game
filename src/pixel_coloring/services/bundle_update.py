"""Update bundled art while migrating masks and keeping an exact recovery copy."""

import hashlib
import json
import os
import shutil

import numpy as np
from PIL import Image

from ..importer.level_writer import read_level


def install_updated_sample(source, path, database):
    painting = read_level(source)
    if not path.exists():
        with database.connect() as con:
            saved = con.execute(
                "SELECT 1 FROM progress WHERE painting_id=?", (painting.id,)
            ).fetchone()
        if saved:
            raise ValueError("Eski seviye dosyası eksik; boyama kaydını korumak için dönüşüm durduruldu")
        shutil.copy2(source, path)
        database.register(painting, path)
        with database.connect() as con:
            con.execute(
                "UPDATE paintings SET title=?,author=?,category=?,width=?,height=?,palette_size=? WHERE id=?",
                (painting.title, painting.author, painting.category, painting.width,
                 painting.height, len(painting.palette), painting.id),
            )
        return
    old_bytes = path.read_bytes()
    new_bytes = source.read_bytes()
    if old_bytes == new_bytes:
        with database.connect() as con:
            dimensions = con.execute(
                "SELECT width,height,palette_size FROM paintings WHERE id=?", (painting.id,)
            ).fetchone()
        if dimensions is None or dimensions == (painting.width, painting.height, len(painting.palette)):
            database.register(painting, path)
            return
        # A process interruption between file replacement and DB commit is retryable.
        for candidate in sorted((path.parent / "backups").glob(painting.id + "-*/*")):
            if candidate.suffix != ".pcolor":
                continue
            previous = read_level(candidate)
            if dimensions == (previous.width, previous.height, len(previous.palette)):
                old_bytes = candidate.read_bytes()
                break
        else:
            raise ValueError("Dönüşüm yedeği bulunamadı; mevcut kayıt korunuyor")
    import io
    old = read_level(io.BytesIO(old_bytes))
    if old.id != painting.id:
        raise ValueError("Güncellenecek resmin kimliği eşleşmiyor")
    backup_dir = path.parent / "backups" / (painting.id + "-" + hashlib.sha256(old_bytes).hexdigest()[:16])
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / path.name
    if not backup.exists():
        backup.write_bytes(old_bytes)
    temp = path.with_suffix(".updating")
    replaced = False
    try:
        with database.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT * FROM paintings WHERE id=?", (painting.id,)).fetchone()
            saved = con.execute("SELECT * FROM progress WHERE painting_id=?", (painting.id,)).fetchone()
            snapshot = backup_dir / "progress.json"
            if not snapshot.exists():
                snapshot.write_text(json.dumps({"painting": row, "progress": [
                    v.hex() if isinstance(v, bytes) else v for v in saved
                ] if saved else None}, ensure_ascii=False), encoding="utf-8")
            if saved:
                if row[4:6] != (old.width, old.height):
                    raise ValueError("Eski resim ve kayıt boyutları eşleşmiyor")
                if saved[5] != 1 or len(saved[6]) != (old.target_map.size + 7) // 8:
                    raise ValueError("Eski boyama kaydı bozuk; dönüşüm uygulanmadı")
                bits = np.unpackbits(np.frombuffer(saved[6], dtype=np.uint8), count=old.target_map.size)
                mask = np.asarray(Image.fromarray(bits.reshape(old.height, old.width)).resize(
                    (painting.width, painting.height), Image.Resampling.NEAREST
                ), dtype=bool)
                count = int(mask.sum())
                rgb = old.palette[max(0, min(len(old.palette) - 1, saved[7]))].astype(np.int32)
                selected = int(np.argmin(((painting.palette.astype(np.int32) - rgb) ** 2).sum(axis=1)))
                con.execute(
                    "UPDATE progress SET progress_blob=?,painted_count=?,completion_percentage=?,"
                    "selected_color=? WHERE painting_id=?",
                    (np.packbits(mask).tobytes(), count, 100 * count / mask.size, selected, painting.id),
                )
            con.execute(
                "UPDATE paintings SET title=?,author=?,category=?,width=?,height=?,palette_size=?,"
                "data_path=? WHERE id=?",
                (painting.title, painting.author, painting.category, painting.width, painting.height,
                 len(painting.palette), str(path), painting.id),
            )
            # Replace before commit; roll back the file as well if the transaction fails.
            temp.write_bytes(new_bytes)
            os.replace(temp, path)
            replaced = True
    except BaseException:
        if replaced:
            temp.write_bytes(old_bytes)
            os.replace(temp, path)
        raise
    finally:
        temp.unlink(missing_ok=True)
    if row is None:
        database.register(painting, path)
