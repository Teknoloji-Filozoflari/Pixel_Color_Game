"""Build optional category pack ZIPs and refresh manifest sha256/bytes.

Usage:
  python3 packaging/build_content_packs.py
  python3 packaging/build_content_packs.py --out-dir dist/content-packs

Upload the resulting ZIP files to a GitHub Release whose tag matches
`release_tag` in resources/packs/manifest.json (default: content-v1).
Asset names must match each pack's `file` field.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "src/pixel_coloring/resources/paintings"
MANIFEST = ROOT / "src/pixel_coloring/resources/packs/manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def build_pack(pack: dict, out_dir: Path) -> Path:
    painting_ids = pack.get("painting_ids") or []
    if not painting_ids:
        raise RuntimeError(f"Pack {pack['id']} has no painting_ids")
    out_dir.mkdir(parents=True, exist_ok=True)
    archive_path = out_dir / pack["file"]
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for painting_id in painting_ids:
            source = GALLERY / f"{painting_id}.pcolor"
            if not source.is_file():
                raise FileNotFoundError(source)
            archive.write(source, arcname=f"{painting_id}.pcolor")
    pack["bytes"] = archive_path.stat().st_size
    pack["sha256"] = sha256_file(archive_path)
    pack["painting_count"] = len(painting_ids)
    return archive_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "dist/content-packs")
    parser.add_argument("--update-manifest", action="store_true", default=True)
    parser.add_argument("--no-update-manifest", action="store_false", dest="update_manifest")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    built = []
    for pack in manifest["packs"]:
        if pack.get("bundled"):
            continue
        path = build_pack(pack, args.out_dir)
        built.append(path)
        print(f"{pack['id']}: {path.name} ({pack['bytes']} bytes)")

    if args.update_manifest:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Updated {MANIFEST.relative_to(ROOT)}")

    print(f"Built {len(built)} pack(s) in {args.out_dir}")
    print(
        "Publish: create GitHub Release "
        f"`{manifest.get('release_tag', 'content-v1')}` and upload these ZIP assets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
