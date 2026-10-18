"""Build the Windows x64 installer and portable ZIP on a Windows host."""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iscc", type=Path, help="Path to Inno Setup 6 ISCC.exe")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Build on Windows; PyInstaller does not cross-compile Windows executables.")
    compiler = args.iscc or Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / (
        "Inno Setup 6/ISCC.exe"
    )
    if not compiler.is_file():
        parser.error("Install Inno Setup 6 or supply --iscc.")
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    subprocess.run([sys.executable, str(ROOT / "packaging/build_bundle.py"),
                    "--dist-dir", str(ROOT / "build/windows")], cwd=ROOT, check=True)
    bundle = ROOT / "build/windows/Piksel-Atolyesi"
    for name in ("LICENSE", "ASSETS_LICENSE.md", "THIRD_PARTY.md", "TELIF-VE-YAYIN-NOTU.md"):
        shutil.copy2(ROOT / name, bundle / name)
    shutil.copytree(ROOT / "LICENSES", bundle / "LICENSES", dirs_exist_ok=True)
    (bundle / "BASLAT.txt").write_text(
        "ZIP dosyasini tamamen cikarin ve Piksel-Atolyesi.exe dosyasini acin.\n"
        "Python kurulumu gerekmez. 900 resim pakete dahildir.\n"
        "Kayitlar Windows kullanici profilinde saklanir.\n"
        "Kaynak kod / Source: https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game\n",
        encoding="utf-8",
    )
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    portable = Path(shutil.make_archive(
        str(output / f"piksel-atolyesi-{version}-windows-x64"), "zip", bundle.parent, bundle.name
    ))
    subprocess.run([str(compiler), f"/DAppVersion={version}", f"/DProjectRoot={ROOT}",
                    str(ROOT / "packaging/windows/setup.iss")], cwd=ROOT, check=True)
    installer = output / f"Piksel-Atolyesi-{version}-Setup-x64.exe"
    if not installer.is_file():
        raise RuntimeError("Windows installer was not produced")
    checksums = []
    for path in (installer, portable):
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        checksums.append(f"{digest}  {path.name}\n")
    (output / "SHA256SUMS").write_text("".join(checksums), encoding="utf-8", newline="\n")
    print(f"Built {installer.name} and {portable.name}")


if __name__ == "__main__":
    main()
