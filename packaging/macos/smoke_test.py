"""Open the packaged macOS app with a temporary data directory."""

import os
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    apps = list((ROOT / 'build/macos/dist').glob('*.app'))
    if len(apps) != 1:
        raise RuntimeError('Expected exactly one macOS app bundle under build/macos/dist')
    app = apps[0]
    executable = app / 'Contents/MacOS' / 'Piksel Atölyesi'
    if not executable.is_file():
        raise RuntimeError(f'missing executable: {executable}')
    with tempfile.TemporaryDirectory(prefix='piksel-macos-') as temporary:
        data = Path(temporary)
        environment = os.environ.copy()
        environment['QT_QPA_PLATFORM'] = 'offscreen'
        subprocess.run(
            [str(executable), '--smoke-test', '--data-dir', str(data)],
            env=environment, check=True, timeout=180,
        )
        with closing(sqlite3.connect(data / 'progress.sqlite3')) as database:
            if database.execute('SELECT COUNT(*) FROM paintings').fetchone()[0] != 900:
                raise RuntimeError('Installed collection is incomplete')
    archives = list((ROOT / 'dist').glob('piksel-atolyesi-*-macos-arm64.zip'))
    if len(archives) != 1:
        raise RuntimeError('Expected exactly one macOS arm64 ZIP in dist/')
    print(f'macOS app smoke verified: {app.name}; archive {archives[0].name}')


if __name__ == '__main__':
    main()
