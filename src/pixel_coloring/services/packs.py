"""Category pack manifest: bundled core vs optional remote downloads."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

RESOURCES = Path(__file__).resolve().parents[1] / "resources"
PACKS_DIR = RESOURCES / "packs"
MANIFEST_PATH = PACKS_DIR / "manifest.json"
GALLERY_DIR = RESOURCES / "paintings"

# Locked product set — also recorded in the shipped manifest.
BUNDLED_CATEGORIES = frozenset({"Doğa", "Hayvanlar", "Fantastik", "Manzaralar", "Şehirler"})
REMOTE_CATEGORIES = frozenset(
    {
        "TÜRKİYE",
        "TÜRK MOTİFLERİ",
        "Harikalar",
        "Araçlar",
        "Teknoloji",
        "Uzay",
        "Spor",
        "Tarih ve Uygarlıklar",
        "Masallar ve Efsaneler",
    }
)

CATEGORY_ORDER = [
    "Doğa",
    "Hayvanlar",
    "Fantastik",
    "Manzaralar",
    "Şehirler",
    "TÜRKİYE",
    "TÜRK MOTİFLERİ",
    "Harikalar",
    "Teknoloji",
    "Araçlar",
    "Uzay",
    "Spor",
    "Tarih ve Uygarlıklar",
    "Masallar ve Efsaneler",
]


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_catalog() -> list[dict]:
    return json.loads((GALLERY_DIR / "catalog.json").read_text(encoding="utf-8"))


def packs() -> list[dict]:
    return list(load_manifest()["packs"])


def pack_by_id(pack_id: str) -> dict | None:
    for pack in packs():
        if pack["id"] == pack_id:
            return pack
    return None


def pack_for_category(category: str) -> dict | None:
    for pack in packs():
        if pack["category"] == category:
            return pack
    return None


def bundled_packs() -> list[dict]:
    return [pack for pack in packs() if pack.get("bundled")]


def downloadable_packs() -> list[dict]:
    return [pack for pack in packs() if not pack.get("bundled")]


def bundled_painting_ids() -> set[str]:
    ids: set[str] = set()
    for pack in bundled_packs():
        ids.update(pack.get("painting_ids") or [])
    if not ids:
        # Fallback if manifest is incomplete: use category labels from the catalog.
        ids = {item["id"] for item in load_catalog() if item.get("category") in BUNDLED_CATEGORIES}
    return ids


def is_bundled_category(category: str) -> bool:
    return category in BUNDLED_CATEGORIES


def pack_download_url(pack: dict, manifest: dict | None = None) -> str:
    meta = manifest or load_manifest()
    base = meta.get("base_url") or ""
    if not base.endswith("/"):
        base += "/"
    return base + pack["file"]


def preview_paths(pack_id: str) -> list[Path]:
    folder = PACKS_DIR / "previews" / pack_id
    if not folder.is_dir():
        return []
    return sorted(folder.glob("*.webp"))


def format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.0f} KB"
    return f"{size / (1024 * 1024):.1f} MB"
