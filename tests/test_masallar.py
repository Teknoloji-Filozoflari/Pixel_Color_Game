"""Masallar ve Efsaneler downloadable pack levels follow the remote 13×7 ladder."""

import json
from collections import Counter
from pathlib import Path

from pixel_coloring.importer.level_writer import read_level, read_thumbnail

ROOT = Path(__file__).parents[1]
GALLERY = ROOT / "src/pixel_coloring/resources/paintings"
CATALOG = json.loads((GALLERY / "catalog.json").read_text(encoding="utf-8"))
CATEGORY = "Masallar ve Efsaneler"
MASALLAR = [item for item in CATALOG if item["category"] == CATEGORY]


def test_masallar_count_and_tiers():
    assert len(MASALLAR) == 91
    assert Counter(item["tier"] for item in MASALLAR) == Counter({tier: 13 for tier in range(1, 8)})
    assert {item["order"] for item in MASALLAR} == set(range(1, 92))


def test_masallar_files_match_catalog():
    for item in MASALLAR:
        path = GALLERY / f"{item['id']}.pcolor"
        painting = read_level(path)
        assert painting.id == item["id"]
        assert painting.category == CATEGORY
        assert painting.width == item["width"]
        assert painting.height == item["height"]
        assert len(painting.palette) == item["colors"]
        assert read_thumbnail(path)


def test_masallar_in_manifest():
    from pixel_coloring.services.packs import REMOTE_CATEGORIES, pack_for_category

    assert CATEGORY in REMOTE_CATEGORIES
    pack = pack_for_category(CATEGORY)
    assert pack is not None
    assert pack["id"] == "cat-masallar"
    assert pack["painting_count"] == 91
    assert set(pack["painting_ids"]) == {item["id"] for item in MASALLAR}
