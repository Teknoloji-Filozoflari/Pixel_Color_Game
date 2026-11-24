"""Import Tarih ve Uygarlıklar using the same verified grid progression as Wonders."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from pixel_coloring.importer.level_writer import read_level, write_level

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "src/pixel_coloring/resources/paintings"
HELPERS = runpy.run_path(str(ROOT / "packaging/import_wonders.py"))
convert = HELPERS["convert"]
progression_plan = HELPERS["progression_plan"]

CATEGORY = "Tarih ve Uygarlıklar"
EXPECTED_TOTAL = 1264  # current catalog (bundled + all shipped remotes)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()

    items = json.loads((args.source / "91-gorsel-envanteri.json").read_text(encoding="utf-8"))
    titles = json.loads((args.source / "titles.json").read_text(encoding="utf-8"))
    assert len(items) == 91
    assert Counter(item["tier"] for item in items) == Counter({tier: 13 for tier in range(1, 8)})
    assert {item["order"] for item in items} == set(range(1, 92))

    source_paths: dict[str, Path] = {}
    verified: dict[str, dict] = {}
    for item in items:
        assert item["category"] == CATEGORY and item["id"].startswith("sample-tarih-")
        source = args.source / item["file"]
        assert source.is_file(), source
        with Image.open(source) as image:
            assert abs(image.width / image.height - 4 / 3) < 0.02, image.size
            source_width, source_height = image.size
            image.verify()
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        source_paths[item["id"]] = source
        verified[item["id"]] = {
            "id": item["id"],
            "title": item["title"],
            "file": item["file"],
            "sha256": digest,
            "source_width": source_width,
            "source_height": source_height,
        }

    catalog_path = GALLERY / "catalog.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    plan = progression_plan(items, catalog, source_paths)

    if args.preview:
        canvas = Image.new("RGB", (960, 7 * 270), "#20252B")
        draw = ImageDraw.Draw(canvas)
        for tier in range(1, 8):
            group = [item for item in plan if item["tier"] == tier]
            for column, item in enumerate([group[0], group[6], group[-1]]):
                painting = convert(source_paths[item["id"]], item)
                image = Image.fromarray(painting.palette[painting.target_map])
                image = ImageOps.contain(image, (320, 240), Image.Resampling.NEAREST)
                x, y = column * 320, (tier - 1) * 270
                canvas.paste(image, (x + (320 - image.width) // 2, y + (240 - image.height) // 2))
                draw.text(
                    (x + 8, y + 246),
                    f"Tier {tier}: {painting.width}x{painting.height}, {len(painting.palette)} colors",
                )
        output = ROOT / "work/tarih-conversion-preview.png"
        output.parent.mkdir(exist_ok=True)
        canvas.save(output)
        print("Validated 91 PNGs. Preview:", output)
        return

    existing = {item["id"]: item for item in catalog}
    baseline = {
        GALLERY / (item["id"] + ".pcolor"): hashlib.sha256(
            (GALLERY / (item["id"] + ".pcolor")).read_bytes()
        ).hexdigest()
        for item in catalog
        if item["id"] not in verified
    }
    staged = ROOT / "work/tarih-levels"
    staged.mkdir(parents=True, exist_ok=True)
    updates = []
    for item in plan:
        painting = convert(source_paths[item["id"]], item)
        path = GALLERY / (painting.id + ".pcolor")
        output = staged / path.name
        write_level(painting, output)
        restored = read_level(output)
        assert restored.id == item["id"] and restored.title == item["title"]
        assert np.array_equal(painting.target_map, restored.target_map)
        assert np.array_equal(painting.palette, restored.palette)
        updates.append((output, path))
        previous = existing.get(painting.id) or {}
        previous_sha = previous.get("source_sha256")
        previous_revision = int(previous.get("revision", 1) or 1)
        source_sha = verified[item["id"]]["sha256"]
        revision = previous_revision + 1 if previous_sha and previous_sha != source_sha else max(previous_revision, 1)
        existing[painting.id] = {
            "id": painting.id,
            "title": painting.title,
            "category": CATEGORY,
            "width": painting.width,
            "height": painting.height,
            "colors": len(painting.palette),
            "cells": int(painting.target_map.size),
            "tier": item["tier"],
            "difficulty": item["difficulty"],
            "order": item["order"],
            "revision": revision,
            "color_budget": item["colors"],
            "source_order": item["source_order"],
            "reference_id": item["reference_id"],
            "complexity_score": item["complexity_score"],
            "reference_cells": item["reference_cells"],
            "conversion_policy": "game-progression-v3",
            "source_sha256": source_sha,
            "source_generated": True,
            "interpretation": "Tarih ve uygarlıkların sanatsal piksel yorumu.",
        }

    for output, path in updates:
        os.replace(output, path)

    catalog = [existing[item["id"]] for item in catalog if item["id"] not in verified] + [
        existing[item["id"]] for item in plan
    ]
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in baseline.items())
    assert len(catalog) == EXPECTED_TOTAL
    temp_catalog = catalog_path.with_suffix(".tmp")
    temp_catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_catalog, catalog_path)

    titles_path = ROOT / "src/pixel_coloring/resources/painting_titles.json"
    title_data = json.loads(titles_path.read_text(encoding="utf-8"))
    title_data.update(titles)
    titles_path.write_text(json.dumps(title_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    envanter = ROOT / "packaging/sources/tarih/envanter.csv"
    lines = ["id,title,file,sha256,source_width,source_height"]
    for item in items:
        entry = verified[item["id"]]
        lines.append(
            f"{entry['id']},{entry['title']},{entry['file']},{entry['sha256']},"
            f"{entry['source_width']},{entry['source_height']}"
        )
    envanter.write_text("\n".join(lines) + "\n", encoding="utf-8")

    report = ROOT / "work/tarih-progression-plan.json"
    report.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Imported Tarih levels:", len(plan), "; total paintings:", len(catalog))


if __name__ == "__main__":
    main()
