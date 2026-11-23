"""Download, verify, and install optional category packs from GitHub Releases."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from types import SimpleNamespace

from .packs import downloadable_packs, load_manifest, pack_by_id, pack_download_url

log = logging.getLogger(__name__)


class PackError(Exception):
    """User-facing pack install failure."""


class PackManager:
    def __init__(self, data_dir: Path, database, gallery: Path | None = None):
        self.data_dir = Path(data_dir)
        self.database = database
        self.paintings_dir = self.data_dir / "paintings"
        self.packs_dir = self.data_dir / "packs"
        self.packs_dir.mkdir(parents=True, exist_ok=True)
        self.paintings_dir.mkdir(parents=True, exist_ok=True)
        if gallery is None:
            gallery = Path(__file__).resolve().parents[1] / "resources/paintings"
        self.gallery = Path(gallery)
        self.manifest = load_manifest()

    def installed_meta(self, pack_id: str) -> dict | None:
        meta_path = self.packs_dir / pack_id / "pack.meta.json"
        if not meta_path.is_file():
            return None
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def is_installed(self, pack_id: str) -> bool:
        pack = pack_by_id(pack_id)
        if pack is None:
            return False
        if pack.get("bundled"):
            return True
        meta = self.installed_meta(pack_id)
        if meta is None:
            return False
        # Require the pack marker and at least one painting file on disk.
        painting_ids = pack.get("painting_ids") or []
        if not painting_ids:
            return True
        return any((self.paintings_dir / f"{pid}.pcolor").is_file() for pid in painting_ids[:3])

    def status(self, pack_id: str) -> str:
        pack = pack_by_id(pack_id)
        if pack is None:
            return "unknown"
        if pack.get("bundled") or self.is_installed(pack_id):
            return "installed"
        return "available"

    def list_downloadable(self) -> list[dict]:
        rows = []
        for pack in downloadable_packs():
            rows.append({**pack, "status": self.status(pack["id"])})
        return rows

    def install_from_zip(self, pack_id: str, archive_path: Path, progress=None) -> dict:
        """Verify and install a local pack ZIP (used by tests and the downloader)."""
        pack = pack_by_id(pack_id)
        if pack is None:
            raise PackError(f"Bilinmeyen paket: {pack_id}")
        if pack.get("bundled"):
            raise PackError("Bu paket uygulamaya dahildir")

        archive_path = Path(archive_path)
        digest = _sha256_file(archive_path)
        expected = (pack.get("sha256") or "").lower()
        if expected and digest != expected.lower():
            raise PackError("Paket bütünlük kontrolü başarısız (SHA-256)")

        staging_root = Path(tempfile.mkdtemp(prefix=f"pack-{pack_id}-", dir=self.data_dir))
        extract_dir = staging_root / "extract"
        extract_dir.mkdir()
        try:
            with zipfile.ZipFile(archive_path) as archive:
                members = [info for info in archive.infolist() if not info.is_dir()]
                total = max(len(members), 1)
                for index, info in enumerate(members):
                    parts = Path(info.filename).parts
                    if ".." in parts or Path(info.filename).is_absolute():
                        raise PackError("Paket yolu güvenli değil")
                    name = Path(info.filename).name
                    if not name.endswith(".pcolor"):
                        raise PackError("Paket beklenmeyen dosyalar içeriyor")
                    # Keep basename only so nested prefixes cannot escape extract_dir.
                    target = extract_dir / name
                    with archive.open(info) as source, open(target, "wb") as dest:
                        shutil.copyfileobj(source, dest)
                    if progress:
                        progress(index + 1, total, "extract")

            painting_ids = pack.get("painting_ids") or []
            extracted = {path.stem: path for path in extract_dir.glob("*.pcolor")}
            missing = [pid for pid in painting_ids if pid not in extracted]
            if missing:
                raise PackError(f"Pakette eksik seviye var: {missing[0]}")
            extra = set(extracted) - set(painting_ids)
            if extra and painting_ids:
                # Allow supersets only when manifest lists a subset; reject unknown IDs.
                raise PackError("Paket katalogda olmayan seviyeler içeriyor")

            registrations = []
            install_ids = painting_ids or list(extracted)
            total = max(len(install_ids), 1)
            for index, painting_id in enumerate(install_ids):
                source = extracted[painting_id]
                dest = self.paintings_dir / f"{painting_id}.pcolor"
                _install_pcolor(source, dest, self.database, registrations)
                if progress:
                    progress(index + 1, total, "install")
            if registrations:
                self.database.register_many(registrations)

            pack_home = self.packs_dir / pack_id
            pack_home.mkdir(parents=True, exist_ok=True)
            meta = {
                "id": pack_id,
                "category": pack["category"],
                "version": pack.get("version", 1),
                "sha256": digest,
                "installed_at": time.time(),
                "painting_count": len(install_ids),
            }
            meta_path = pack_home / "pack.meta.json"
            tmp_meta = pack_home / "pack.meta.json.tmp"
            tmp_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(tmp_meta, meta_path)
            return meta
        finally:
            shutil.rmtree(staging_root, ignore_errors=True)

    def download_and_install(self, pack_id: str, progress=None) -> dict:
        pack = pack_by_id(pack_id)
        if pack is None:
            raise PackError(f"Bilinmeyen paket: {pack_id}")
        if self.is_installed(pack_id):
            return self.installed_meta(pack_id) or {"id": pack_id, "status": "installed"}

        url = pack_download_url(pack, self.manifest)
        staging = Path(tempfile.mkdtemp(prefix=f"dl-{pack_id}-", dir=self.data_dir))
        archive_path = staging / pack["file"]
        try:
            _download(url, archive_path, expected_bytes=pack.get("bytes"), progress=progress)
            if progress:
                progress(1, 1, "verify")
            return self.install_from_zip(pack_id, archive_path, progress=progress)
        except urllib.error.URLError as exc:
            raise PackError(f"İndirme başarısız: {exc.reason}") from exc
        except PackError:
            raise
        except Exception as exc:
            raise PackError(str(exc)) from exc
        finally:
            shutil.rmtree(staging, ignore_errors=True)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path, expected_bytes=None, progress=None) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "PikselAtolyesi/0.17"})
    with urllib.request.urlopen(request, timeout=120) as response:
        total = expected_bytes or int(response.headers.get("Content-Length") or 0) or None
        done = 0
        tmp = destination.with_suffix(destination.suffix + ".part")
        with open(tmp, "wb") as handle:
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(done, total, "download")
        os.replace(tmp, destination)


def _install_pcolor(source: Path, dest: Path, database, registrations: list) -> None:
    """Copy a level into paintings/ and queue DB registration (atomic replace)."""
    from .bundle_update import install_updated_sample

    with zipfile.ZipFile(source) as archive:
        meta = json.loads(archive.read("metadata.json"))
        palette = json.loads(archive.read("palette.json"))
    painting = SimpleNamespace(
        **{key: meta.get(key, "") for key in ("id", "title", "author", "category", "width", "height")},
        palette=palette,
    )
    revision = int(meta.get("revision", 1) or 1)

    with database.connect() as con:
        saved = con.execute(
            "SELECT 1 FROM progress WHERE painting_id=?", (painting.id,)
        ).fetchone() is not None
        registered = con.execute(
            "SELECT 1 FROM paintings WHERE id=?", (painting.id,)
        ).fetchone() is not None

    if revision > 1 and (dest.exists() or saved or registered):
        install_updated_sample(source, dest, database)
        return

    tmp = dest.with_suffix(".pcolor.partial")
    shutil.copy2(source, tmp)
    os.replace(tmp, dest)
    registrations.append((painting, dest))
