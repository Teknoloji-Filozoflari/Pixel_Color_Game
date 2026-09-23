"""Remove an imported game copy without touching the user's original image."""

import logging
import uuid
from pathlib import Path

log = logging.getLogger(__name__)


def delete_imported(database, painting_id, paintings_dir):
    if painting_id.startswith("sample-"):
        raise ValueError("Hazır koleksiyon resimleri silinemez")
    _delete_game_copy(database, painting_id, paintings_dir)


def remove_retired_samples(database, paintings_dir):
    """Remove only the six withdrawn starter pictures, never imported artwork."""
    retired = tuple(f"sample-{i}-v1" for i in range(6))
    with database.connect() as con:
        ids = [row[0] for row in con.execute(
            "SELECT id FROM paintings WHERE id IN (?,?,?,?,?,?) AND palette_size < 16", retired
        )]
    for painting_id in ids:
        _delete_game_copy(database, painting_id, paintings_dir)


def _delete_game_copy(database, painting_id, paintings_dir):
    staged = None
    path = None
    try:
        with database.connect() as con:
            row = con.execute("SELECT data_path FROM paintings WHERE id=?", (painting_id,)).fetchone()
            if row is None:
                raise ValueError("Resim bulunamadı")
            path = Path(row[0]).resolve()
            if path.parent != Path(paintings_dir).resolve() or path.suffix != ".pcolor":
                raise ValueError("Resim dosyası oyunun resim klasöründe değil")
            if path.exists():
                staged = path.with_name(f"{uuid.uuid4()}.deleted")
                path.rename(staged)
            con.execute("DELETE FROM progress WHERE painting_id=?", (painting_id,))
            con.execute("DELETE FROM achievements WHERE id=?", ("complete:" + painting_id,))
            con.execute("DELETE FROM paintings WHERE id=?", (painting_id,))
    except Exception:
        if staged is not None and staged.exists():
            staged.rename(path)
        raise
    if staged is not None:
        try:
            staged.unlink()
        except OSError:
            log.warning("Silinen resmin geçici dosyası temizlenemedi: %s", staged, exc_info=True)
