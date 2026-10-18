"""Install, open and uninstall the actual Windows release in a temporary folder."""

import os
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    installers = list((ROOT / "dist").glob("*-Setup-x64.exe"))
    if len(installers) != 1:
        raise RuntimeError("Expected exactly one Windows installer")
    with tempfile.TemporaryDirectory(prefix="piksel-windows-") as temporary:
        root = Path(temporary)
        installed = root / "Installed Game"
        data = root / "Player Data"
        subprocess.run([str(installers[0]), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                        "/SP-", f"/DIR={installed}", f"/LOG={root / 'install.log'}"],
                       check=True, timeout=180)
        # A native Windows window, not only Qt's offscreen backend.
        environment = os.environ.copy()
        environment.pop("QT_QPA_PLATFORM", None)
        subprocess.run([str(installed / "Piksel-Atolyesi.exe"), "--smoke-test", "--data-dir", str(data)],
                       env=environment, check=True, timeout=120)
        with sqlite3.connect(data / "progress.sqlite3") as database:
            if database.execute("SELECT COUNT(*) FROM paintings").fetchone()[0] != 900:
                raise RuntimeError("Installed collection is incomplete")
        subprocess.run([str(installed / "unins000.exe"), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
                       check=True, timeout=120)
        if not (data / "progress.sqlite3").is_file():
            raise RuntimeError("Uninstall removed player data")
    print("Windows installer, native startup, 900 paintings and uninstall verified")


if __name__ == "__main__":
    main()
