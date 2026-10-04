"""Build and verify the Python/Qt bundle used by RPM and Snap packages."""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def validate_resources(bundle: Path) -> None:
    """Reject a bundle missing the game's complete 900-painting collection."""
    resources = bundle / "_internal/pixel_coloring/resources"
    gallery = resources / "paintings"
    catalog = json.loads((gallery / "catalog.json").read_text(encoding="utf-8"))
    identifiers = {item["id"] for item in catalog}
    if len(catalog) != 900 or len(identifiers) != 900:
        raise RuntimeError("The bundled catalog must contain 900 unique paintings")
    if {file.stem for file in gallery.glob("*.pcolor")} != identifiers:
        raise RuntimeError("The bundled paintings do not match the catalog")
    if not (resources / "icons/piksel-atolyesi.png").is_file():
        raise RuntimeError("The bundled application icon is missing")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, default=ROOT / "build/bundle")
    args = parser.parse_args()
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
         "--workpath", str(ROOT / "build/bundle-work"),
         "--distpath", str(args.dist_dir.resolve()),
         str(ROOT / "packaging/appimage/piksel-atolyesi.spec")],
        cwd=ROOT, check=True,
    )
    bundle = args.dist_dir.resolve() / "piksel-atolyesi"
    validate_resources(bundle)
    with TemporaryDirectory(prefix="piksel-bundle-smoke-") as temporary:
        data = Path(temporary)
        environment = os.environ.copy()
        environment["QT_QPA_PLATFORM"] = "offscreen"
        subprocess.run(
            [str(bundle / "piksel-atolyesi"), "--smoke-test", "--data-dir", str(data)],
            env=environment, check=True, timeout=120,
        )
        with sqlite3.connect(data / "progress.sqlite3") as database:
            if database.execute("SELECT COUNT(*) FROM paintings").fetchone()[0] != 900:
                raise RuntimeError("Installed collection is incomplete")
    print(f"Verified bundle: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
