"""Build and verify the Python/Qt bundle used by Windows, RPM and Snap."""

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "src/pixel_coloring/resources/packs/manifest.json"


def bundled_painting_ids() -> set[str]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ids: set[str] = set()
    for pack in manifest["packs"]:
        if pack.get("bundled"):
            ids.update(pack.get("painting_ids") or [])
    return ids


def strip_remote_paintings(bundle: Path) -> None:
    """Keep catalog/manifest metadata but ship only bundled .pcolor files."""
    gallery = bundle / "_internal/pixel_coloring/resources/paintings"
    keep = bundled_painting_ids()
    for path in gallery.glob("*.pcolor"):
        if path.stem not in keep:
            path.unlink()


def validate_resources(bundle: Path) -> None:
    """Reject a bundle whose bundled paintings do not match the pack manifest."""
    resources = bundle / "_internal/pixel_coloring/resources"
    gallery = resources / "paintings"
    catalog = json.loads((gallery / "catalog.json").read_text(encoding="utf-8"))
    identifiers = {item["id"] for item in catalog}
    if len(catalog) != 1355 or len(identifiers) != 1355:
        raise RuntimeError("The source catalog must contain 1355 unique paintings")
    keep = bundled_painting_ids()
    present = {file.stem for file in gallery.glob("*.pcolor")}
    if present != keep:
        missing = sorted(keep - present)
        extra = sorted(present - keep)
        raise RuntimeError(
            "The bundled paintings do not match the core pack set"
            + (f"; missing={missing[:3]}" if missing else "")
            + (f"; extra={extra[:3]}" if extra else "")
        )
    if not (resources / "packs/manifest.json").is_file():
        raise RuntimeError("The pack manifest is missing from the bundle")
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
    name = "Piksel-Atolyesi" if sys.platform == "win32" else "piksel-atolyesi"
    executable = name + (".exe" if sys.platform == "win32" else "")
    bundle = args.dist_dir.resolve() / name
    strip_remote_paintings(bundle)
    validate_resources(bundle)
    expected = len(bundled_painting_ids())
    with TemporaryDirectory(prefix="piksel-bundle-smoke-") as temporary:
        data = Path(temporary)
        environment = os.environ.copy()
        environment["QT_QPA_PLATFORM"] = "offscreen"
        subprocess.run(
            [str(bundle / executable), "--smoke-test", "--data-dir", str(data)],
            env=environment, check=True, timeout=120,
        )
        with closing(sqlite3.connect(data / "progress.sqlite3")) as database:
            if database.execute("SELECT COUNT(*) FROM paintings").fetchone()[0] != expected:
                raise RuntimeError("Installed collection is incomplete")
    print(f"Verified bundle: {bundle} ({expected} core paintings)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
