"""Build the macOS .app bundle and portable ZIP on a macOS host."""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def make_icns(png: Path, destination: Path) -> Path:
    """Create an .icns from the app PNG using macOS iconutil."""
    with tempfile.TemporaryDirectory(prefix='piksel-icon-') as temporary:
        iconset = Path(temporary) / 'PikselAtolyesi.iconset'
        iconset.mkdir()
        for size in (16, 32, 64, 128, 256, 512):
            for scale, suffix in ((1, ''), (2, '@2x')):
                pixels = size * scale
                if pixels > 1024:
                    continue
                output = iconset / f'icon_{size}x{size}{suffix}.png'
                subprocess.run(
                    ['sips', '-z', str(pixels), str(pixels), str(png), '--out', str(output)],
                    check=True, capture_output=True,
                )
        subprocess.run(['iconutil', '-c', 'icns', str(iconset), '-o', str(destination)], check=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    if sys.platform != 'darwin':
        parser.error('Build on macOS; PyInstaller does not cross-compile macOS app bundles.')
    version = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    build_root = ROOT / 'build/macos'
    if build_root.exists():
        shutil.rmtree(build_root)
    build_root.mkdir(parents=True)
    icns = make_icns(
        ROOT / 'src/pixel_coloring/resources/icons/piksel-atolyesi.png',
        build_root / 'piksel-atolyesi.icns',
    )
    env = os.environ.copy()
    env['PIKSEL_MACOS_ICNS'] = str(icns)
    env['PIKSEL_APP_VERSION'] = version
    subprocess.run(
        [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm',
         '--workpath', str(ROOT / 'build/macos-work'),
         '--distpath', str(build_root / 'dist'),
         str(ROOT / 'packaging/macos/piksel-atolyesi.spec')],
        cwd=ROOT, check=True, env=env,
    )
    app = build_root / 'dist' / 'Piksel Atölyesi.app'
    if not app.is_dir():
        raise RuntimeError('macOS app bundle was not produced')
    resources = app / 'Contents/Resources/pixel_coloring/resources'
    if not (resources / 'paintings/catalog.json').is_file():
        # onedir/COLLECT layout may nest under Frameworks/MacOS support paths
        resources = app / 'Contents/Frameworks/pixel_coloring/resources'
    gallery = None
    for candidate in app.rglob('catalog.json'):
        if candidate.parent.name == 'paintings':
            gallery = candidate.parent
            break
    if gallery is None:
        raise RuntimeError('Bundled painting catalog is missing from the macOS app')
    catalog_count = len([path for path in gallery.glob('*.pcolor')])
    if catalog_count != 900:
        raise RuntimeError(f'Expected 900 paintings in the macOS app, found {catalog_count}')
    for name in ('LICENSE', 'ASSETS_LICENSE.md', 'THIRD_PARTY.md', 'TELIF-VE-YAYIN-NOTU.md'):
        shutil.copy2(ROOT / name, app / 'Contents/Resources' / name)
    shutil.copytree(ROOT / 'LICENSES', app / 'Contents/Resources/LICENSES', dirs_exist_ok=True)
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    zip_stem = output / f'piksel-atolyesi-{version}-macos-arm64'
    if zip_stem.with_suffix('.zip').exists():
        zip_stem.with_suffix('.zip').unlink()
    portable = Path(shutil.make_archive(str(zip_stem), 'zip', app.parent, app.name))
    # Prefer Apple Silicon artifact naming; Intel runners can rename via CI matrix.
    arch = os.uname().machine
    if arch == 'x86_64':
        renamed = output / f'piksel-atolyesi-{version}-macos-x64.zip'
        portable.replace(renamed)
        portable = renamed
    checksum = hashlib.sha256(portable.read_bytes()).hexdigest()
    (output / 'SHA256SUMS').write_text(f'{checksum}  {portable.name}\n', encoding='utf-8', newline='\n')
    print(f'Built {portable.name}')


if __name__ == '__main__':
    main()
