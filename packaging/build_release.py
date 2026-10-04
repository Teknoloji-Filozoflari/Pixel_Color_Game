"""Build clean source and optional Windows portable archives without player data."""
import argparse
import hashlib
import json
import shutil
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('src', 'tests', 'docs', 'LICENSES', 'packaging', 'snap', '.github')
FILES = ('pyproject.toml', 'README.md', 'LICENSE', 'ASSETS_LICENSE.md', 'KOLEKSIYON.md',
         'THIRD_PARTY.md', 'TELIF-VE-YAYIN-NOTU.md', 'CONTRIBUTING.md', 'requirements-tested.txt',
         '.gitignore', '.dockerignore', 'flake.nix', 'flake.lock', 'default.nix', 'MANIFEST.in', 'run.py', 'start.bat', 'start.sh', 'install.sh', 'uninstall.sh')
EXCLUDED = {'__pycache__', '.git', '.tools', 'work', 'local-data', 'runtime',
            '.pytest_cache', '.ruff_cache', '.venv', 'venv'}


def archive(folder, path):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for file in sorted(folder.rglob('*')):
            if file.is_file():
                output.write(file, str(Path(folder.name) / file.relative_to(folder)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, help='Embedded CPython directory for Windows')
    args = parser.parse_args()
    version = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    staging = ROOT / 'work' / f'release-{version}'
    source = staging / f'piksel-atolyesi-{version}-source'
    if source.exists():
        raise SystemExit(f'Staging already exists: {source}; review it before rebuilding.')
    source.mkdir(parents=True)
    candidates = [ROOT / name for name in FILES]
    for directory in DIRECTORIES:
        candidates.extend(file for file in (ROOT / directory).rglob('*') if file.is_file())
    for file in candidates:
        relative = file.relative_to(ROOT)
        if EXCLUDED.intersection(relative.parts) or file.name.endswith(
                ('.pyc', '.log', '.sqlite3', '.sqlite3-wal', '.sqlite3-shm')):
            continue
        if file.name in {'.env', 'credentials.json'}:
            continue
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target)
    gallery = source / 'src/pixel_coloring/resources/paintings'
    catalog = json.loads((gallery / 'catalog.json').read_text(encoding='utf-8'))
    assert len(catalog) == len({item['id'] for item in catalog}) == 900
    assert {file.stem for file in gallery.glob('*.pcolor')} == {item['id'] for item in catalog}
    for item in catalog:
        with zipfile.ZipFile(gallery / (item['id'] + '.pcolor')) as level:
            assert set(level.namelist()) == {'metadata.json', 'palette.json', 'target.npy', 'preview.webp'}
    outputs = [output / f'{source.name}.zip']
    archive(source, outputs[0])
    if args.runtime:
        runtime = args.runtime.resolve()
        assert (runtime / 'python.exe').is_file() and (runtime / 'python313._pth').is_file()
        portable = staging / f'piksel-atolyesi-{version}-windows-x64'
        shutil.copytree(source, portable)
        installed = portable / '.tools/python'
        shutil.copytree(runtime, installed, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        (installed / 'python313._pth').write_text(
            'python313.zip\n.\nLib/site-packages\n../../src\nimport site\n', encoding='utf-8')
        (portable / 'OYUNU-BASLAT.txt').write_text(
            'ZIP dosyasını tamamen çıkarın ve start.bat dosyasını açın.\n'
            'Python kurulumu gerekmez. 900 resim sıfır boyama ilerlemesiyle başlar.\n'
            'Kayıtlar kullanıcı profilinizde saklanır; pakette kişisel kayıt yoktur.\n', encoding='utf-8')
        outputs.append(output / f'{portable.name}.zip')
        archive(portable, outputs[-1])
    sums = '\n'.join(f'{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.name}' for file in outputs)
    (output / 'SHA256SUMS').write_text(sums + '\n', encoding='utf-8')
    print(f'Validated {len(catalog)} levels without saved progress. Staging: {source}')
    for file in outputs:
        print(f'{file.name}: {file.stat().st_size / 1024 ** 2:.1f} MiB')


if __name__ == '__main__':
    main()
