"""Spor downloadable pack levels follow the remote 13×7 ladder."""

import json
from collections import Counter
from pathlib import Path

from pixel_coloring.importer.level_writer import read_level, read_thumbnail

ROOT = Path(__file__).parents[1]
GALLERY = ROOT / "src/pixel_coloring/resources/paintings"
CATALOG = json.loads((GALLERY / "catalog.json").read_text(encoding="utf-8"))
SPOR = [item for item in CATALOG if item["category"] == "Spor"]


def test_spor_count_and_tiers():
    assert len(SPOR) == 91
    assert Counter(item["tier"] for item in SPOR) == Counter({tier: 13 for tier in range(1, 8)})
    assert {item["order"] for item in SPOR} == set(range(1, 92))


def test_spor_files_match_catalog():
    for item in SPOR:
        path = GALLERY / f"{item['id']}.pcolor"
        painting = read_level(path)
        assert painting.id == item["id"]
        assert painting.category == "Spor"
        assert painting.width == item["width"]
        assert painting.height == item["height"]
        assert len(painting.palette) == item["colors"]
        assert read_thumbnail(path)


def test_spor_in_manifest():
    from pixel_coloring.services.packs import REMOTE_CATEGORIES, pack_for_category

    assert "Spor" in REMOTE_CATEGORIES
    pack = pack_for_category("Spor")
    assert pack is not None
    assert pack["id"] == "cat-spor"
    assert pack["painting_count"] == 91
    assert set(pack["painting_ids"]) == {item["id"] for item in SPOR}
