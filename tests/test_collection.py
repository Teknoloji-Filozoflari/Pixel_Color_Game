import json
import zipfile
from pathlib import Path


PAINTINGS = Path(__file__).parents[1] / "src/pixel_coloring/resources/paintings"


def test_catalog_matches_bundled_files():
    catalog = json.loads((PAINTINGS / "catalog.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in catalog]

    assert len(catalog) == 536
    assert len(ids) == len(set(ids))
    assert {path.stem for path in PAINTINGS.glob("*.pcolor")} == set(ids)


def test_bundled_metadata_matches_catalog():
    catalog = json.loads((PAINTINGS / "catalog.json").read_text(encoding="utf-8"))

    for item in catalog:
        with zipfile.ZipFile(PAINTINGS / f"{item['id']}.pcolor") as archive:
            metadata = json.loads(archive.read("metadata.json"))
            palette = json.loads(archive.read("palette.json"))
        assert (metadata["id"], metadata["width"], metadata["height"], len(palette)) == (
            item["id"], item["width"], item["height"], item["colors"],
        )
