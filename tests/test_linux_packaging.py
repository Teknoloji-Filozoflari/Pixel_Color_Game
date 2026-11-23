import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("build_bundle", ROOT / "packaging/build_bundle.py")
build_bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_bundle)


def _bundle_with_core(tmp_path):
    resources = tmp_path / "_internal/pixel_coloring/resources"
    gallery = resources / "paintings"
    gallery.mkdir(parents=True)
    catalog = [{"id": f"painting-{index}"} for index in range(1173)]
    (gallery / "catalog.json").write_text(json.dumps(catalog))
    keep = build_bundle.bundled_painting_ids()
    # Map real bundled IDs onto placeholder files for validate_resources.
    for value in keep:
        (gallery / f"{value}.pcolor").touch()
    # Catalog must still list 1173 unique ids — use real keep ids plus fillers.
    real_catalog = [{"id": painting_id} for painting_id in sorted(keep)]
    fillers = [{"id": f"remote-filler-{index}"} for index in range(1173 - len(keep))]
    (gallery / "catalog.json").write_text(json.dumps(real_catalog + fillers))
    packs = resources / "packs"
    packs.mkdir(parents=True)
    (packs / "manifest.json").write_text((ROOT / "src/pixel_coloring/resources/packs/manifest.json").read_text())
    icon = resources / "icons/piksel-atolyesi.png"
    icon.parent.mkdir()
    icon.touch()
    return gallery, keep


def test_bundle_requires_complete_collection_and_icon(tmp_path):
    gallery, keep = _bundle_with_core(tmp_path)
    build_bundle.validate_resources(tmp_path)
    victim = next(iter(keep))
    (gallery / f"{victim}.pcolor").unlink()
    with pytest.raises(RuntimeError, match="do not match"):
        build_bundle.validate_resources(tmp_path)


def test_bundle_rejects_duplicate_catalog_identifiers(tmp_path):
    gallery = tmp_path / "_internal/pixel_coloring/resources/paintings"
    gallery.mkdir(parents=True)
    (gallery / "catalog.json").write_text(json.dumps([{"id": "duplicate"}] * 1173))
    (tmp_path / "_internal/pixel_coloring/resources/packs").mkdir(parents=True)
    (tmp_path / "_internal/pixel_coloring/resources/packs/manifest.json").write_text("{}")
    with pytest.raises(RuntimeError, match="1173 unique"):
        build_bundle.validate_resources(tmp_path)
