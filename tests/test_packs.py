"""Optional category pack install, hash checks, and offline core behaviour."""

import hashlib
import zipfile
from pathlib import Path

import pytest

from pixel_coloring.persistence.database import Database
from pixel_coloring.services import pack_manager as pack_manager_module
from pixel_coloring.services.pack_manager import PackError, PackManager
from pixel_coloring.services.packs import (
    BUNDLED_CATEGORIES,
    bundled_painting_ids,
    downloadable_packs,
    load_manifest,
)
from pixel_coloring.services.samples import ensure_samples

ROOT = Path(__file__).parents[1]
GALLERY = ROOT / "src/pixel_coloring/resources/paintings"


@pytest.fixture
def tiny_pack(tmp_path, monkeypatch):
    """Build a one-painting pack and point PackManager at it."""
    manifest = load_manifest()
    original = next(p for p in manifest["packs"] if p["id"] == "cat-teknoloji")
    painting_id = original["painting_ids"][0]
    source = GALLERY / f"{painting_id}.pcolor"
    assert source.is_file()

    archive = tmp_path / "tiny-teknoloji.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(source, arcname=f"{painting_id}.pcolor")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    fake = {
        **original,
        "painting_ids": [painting_id],
        "painting_count": 1,
        "sha256": digest,
        "bytes": archive.stat().st_size,
        "file": archive.name,
    }

    def fake_pack_by_id(pack_id):
        if pack_id == fake["id"]:
            return fake
        return next((p for p in manifest["packs"] if p["id"] == pack_id), None)

    monkeypatch.setattr(pack_manager_module, "pack_by_id", fake_pack_by_id)
    return {"pack": fake, "archive": archive, "painting_id": painting_id}


def test_manifest_splits_bundled_and_remote():
    manifest = load_manifest()
    assert manifest["schema"] == 1
    assert "releases/download/" in manifest["base_url"]
    bundled = [p for p in manifest["packs"] if p.get("bundled")]
    remote = [p for p in manifest["packs"] if not p.get("bundled")]
    assert {p["category"] for p in bundled} == BUNDLED_CATEGORIES
    assert len(bundled_painting_ids()) == 455
    assert len(remote) == 9
    for pack in remote:
        assert pack["sha256"]
        assert pack["file"].endswith(".zip")
        assert pack["painting_count"] == len(pack["painting_ids"])


def test_ensure_samples_installs_only_bundled_core(tmp_path):
    database = Database(tmp_path / "progress.sqlite3")
    folder = tmp_path / "paintings"
    folder.mkdir()
    ensure_samples(folder, database)
    with database.connect() as con:
        count = con.execute("SELECT COUNT(*) FROM paintings").fetchone()[0]
        categories = {
            row[0] for row in con.execute("SELECT DISTINCT category FROM paintings")
        }
    assert count == len(bundled_painting_ids())
    assert categories == BUNDLED_CATEGORIES
    assert not (folder / f"{downloadable_packs()[0]['painting_ids'][0]}.pcolor").exists()


def test_install_pack_from_zip_registers_and_is_idempotent(tmp_path, tiny_pack):
    database = Database(tmp_path / "progress.sqlite3")
    folder = tmp_path / "paintings"
    folder.mkdir()
    ensure_samples(folder, database)

    manager = PackManager(tmp_path, database)
    meta = manager.install_from_zip(tiny_pack["pack"]["id"], tiny_pack["archive"])
    assert meta["id"] == tiny_pack["pack"]["id"]
    assert manager.is_installed(tiny_pack["pack"]["id"])
    assert (folder / f"{tiny_pack['painting_id']}.pcolor").is_file()
    with database.connect() as con:
        row = con.execute(
            "SELECT category FROM paintings WHERE id=?", (tiny_pack["painting_id"],)
        ).fetchone()
    assert row[0] == "Teknoloji"

    again = manager.install_from_zip(tiny_pack["pack"]["id"], tiny_pack["archive"])
    assert again["id"] == tiny_pack["pack"]["id"]


def test_install_rejects_bad_hash(tmp_path, tiny_pack, monkeypatch):
    database = Database(tmp_path / "progress.sqlite3")
    manager = PackManager(tmp_path, database)
    bad = {**tiny_pack["pack"], "sha256": "0" * 64}
    monkeypatch.setattr(
        pack_manager_module,
        "pack_by_id",
        lambda pack_id: bad if pack_id == bad["id"] else None,
    )
    with pytest.raises(PackError, match="SHA-256"):
        manager.install_from_zip(tiny_pack["pack"]["id"], tiny_pack["archive"])


def test_offline_core_categories_remain_playable_without_packs(tmp_path):
    """No network and no pack ZIPs: bundled categories still install."""
    database = Database(tmp_path / "progress.sqlite3")
    folder = tmp_path / "paintings"
    folder.mkdir()
    ensure_samples(folder, database)
    manager = PackManager(tmp_path, database)
    assert all(not manager.is_installed(p["id"]) for p in downloadable_packs())
    with database.connect() as con:
        assert con.execute("SELECT COUNT(*) FROM paintings").fetchone()[0] == 455
