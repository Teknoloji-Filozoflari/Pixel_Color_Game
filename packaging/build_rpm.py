"""Package a verified PyInstaller bundle for Fedora 43."""

import shutil
import subprocess
import tarfile
import tomllib
from pathlib import Path
from tempfile import TemporaryDirectory

from build_bundle import ROOT, validate_resources


def stage_payload(stage: Path, bundle: Path) -> None:
    validate_resources(bundle)
    shutil.copytree(bundle, stage / "usr/lib/piksel-atolyesi")
    files = {
        "packaging/deb/piksel-atolyesi": "usr/bin/piksel-atolyesi",
        "packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.desktop":
            "usr/share/applications/io.github.teknolojifilozoflari.PixelColorGame.desktop",
        "packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml":
            "usr/share/metainfo/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml",
        "src/pixel_coloring/resources/icons/piksel-atolyesi.png":
            "usr/share/icons/hicolor/512x512/apps/piksel-atolyesi.png",
    }
    for source, target in files.items():
        destination = stage / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source, destination)
    docs = stage / "usr/share/doc/piksel-atolyesi"
    docs.mkdir(parents=True)
    for name in ("LICENSE", "ASSETS_LICENSE.md", "THIRD_PARTY.md", "TELIF-VE-YAYIN-NOTU.md"):
        shutil.copy2(ROOT / name, docs / name)
    shutil.copytree(ROOT / "LICENSES", docs / "LICENSES")


def main() -> None:
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    with TemporaryDirectory(prefix="piksel-rpm-") as temporary:
        top = Path(temporary)
        for name in ("BUILD", "BUILDROOT", "RPMS", "SOURCES", "SPECS", "SRPMS"):
            (top / name).mkdir()
        stage_payload(top / "payload", ROOT / "build/bundle/piksel-atolyesi")
        with tarfile.open(top / "SOURCES/payload.tar.gz", "w:gz") as archive:
            archive.add(top / "payload/usr", arcname="usr")
        subprocess.run(
            ["rpmbuild", "-bb", "--define", f"_topdir {top}", "--define",
             f"app_version {version}", str(ROOT / "packaging/rpm/piksel-atolyesi.spec")],
            check=True,
        )
        output = ROOT / "dist"
        output.mkdir(exist_ok=True)
        for package in (top / "RPMS").rglob("*.rpm"):
            shutil.copy2(package, output / package.name)
            print(output / package.name)


if __name__ == "__main__":
    main()
