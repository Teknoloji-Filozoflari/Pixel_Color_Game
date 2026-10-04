import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("build_bundle", ROOT / "packaging/build_bundle.py")
build_bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_bundle)


def test_bundle_requires_complete_collection_and_icon(tmp_path):
    resources = tmp_path / "_internal/pixel_coloring/resources"
    gallery = resources / "paintings"
    gallery.mkdir(parents=True)
    identifiers = [f"painting-{index}" for index in range(900)]
    (gallery / "catalog.json").write_text(json.dumps([{"id": value} for value in identifiers]))
    for value in identifiers:
        (gallery / f"{value}.pcolor").touch()
    icon = resources / "icons/piksel-atolyesi.png"
    icon.parent.mkdir()
    icon.touch()
    build_bundle.validate_resources(tmp_path)
    (gallery / "painting-1.pcolor").unlink()
    with pytest.raises(RuntimeError, match="do not match"):
        build_bundle.validate_resources(tmp_path)


def test_bundle_rejects_duplicate_catalog_identifiers(tmp_path):
    gallery = tmp_path / "_internal/pixel_coloring/resources/paintings"
    gallery.mkdir(parents=True)
    (gallery / "catalog.json").write_text(json.dumps([{"id": "duplicate"}] * 900))
    with pytest.raises(RuntimeError, match="900 unique"):
        build_bundle.validate_resources(tmp_path)
