"""Build a clean source archive without player data, caches or local environments."""

import hashlib
import json
import shutil
import tempfile
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ('src', 'tests', 'docs', 'LICENSES', 'packaging', 'snap', '.github')
FILES = ('pyproject.toml', 'README.md', 'LICENSE', 'ASSETS_LICENSE.md', 'KOLEKSIYON.md',
         'THIRD_PARTY.md', 'TELIF-VE-YAYIN-NOTU.md', 'CONTRIBUTING.md', 'requirements-tested.txt',
         '.gitignore', '.dockerignore', 'flake.nix', 'flake.lock', 'default.nix', 'MANIFEST.in',
         'run.py', 'start.bat', 'start.sh', 'install.sh', 'uninstall.sh')
EXCLUDED = {'__pycache__', '.git', '.tools', 'work', 'local-data', 'runtime',
            '.pytest_cache', '.ruff_cache', '.venv', 'venv', 'build', 'dist', '.agents', '.codex'}


def include_source(relative):
    return not (
        EXCLUDED.intersection(relative.parts)
        or any(part.endswith('.egg-info') for part in relative.parts)
        or relative.name.endswith(('.pyc', '.log', '.sqlite3', '.sqlite3-wal', '.sqlite3-shm', '.exe'))
        or relative.name == '.env' or relative.name.startswith('.env.')
        or relative.name == 'credentials.json'
    )


def archive(folder, path):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for file in sorted(folder.rglob('*')):
            if file.is_file():
                output.write(file, str(Path(folder.name) / file.relative_to(folder)))


def main():
    version = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    # Staging is disposable and separate from any existing developer work directory.
    with tempfile.TemporaryDirectory(prefix='piksel-source-') as temporary:
        source = Path(temporary) / f'piksel-atolyesi-{version}-source'
        source.mkdir()
        candidates = [ROOT / name for name in FILES]
        for directory in DIRECTORIES:
            candidates.extend(file for file in (ROOT / directory).rglob('*') if file.is_file())
        for file in candidates:
            relative = file.relative_to(ROOT)
            if not include_source(relative):
                continue
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, target)
        gallery = source / 'src/pixel_coloring/resources/paintings'
        catalog = json.loads((gallery / 'catalog.json').read_text(encoding='utf-8'))
        if len(catalog) != 900 or len({item['id'] for item in catalog}) != 900:
            raise RuntimeError('The source catalog must contain 900 unique paintings')
        if {file.stem for file in gallery.glob('*.pcolor')} != {item['id'] for item in catalog}:
            raise RuntimeError('Source paintings do not match the catalog')
        for item in catalog:
            with zipfile.ZipFile(gallery / (item['id'] + '.pcolor')) as level:
                if set(level.namelist()) != {'metadata.json', 'palette.json', 'target.npy', 'preview.webp'}:
                    raise RuntimeError(f'Unexpected level content: {item["id"]}')
        package = output / f'{source.name}.zip'
        archive(source, package)
    with package.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    (output / 'SHA256SUMS').write_text(f'{digest}  {package.name}\n', encoding='utf-8', newline='\n')
    print(f'Validated {len(catalog)} levels without saved progress.')
    print(f'{package.name}: {package.stat().st_size / 1024 ** 2:.1f} MiB')


if __name__ == '__main__':
    main()
