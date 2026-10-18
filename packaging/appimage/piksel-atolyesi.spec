import sys
from pathlib import Path


project_root = Path(SPECPATH).parents[1]
source_root = project_root / "src"
resources = source_root / "pixel_coloring" / "resources"
application_name = "Piksel-Atolyesi" if sys.platform == "win32" else "piksel-atolyesi"

a = Analysis(
    [str(source_root / "pixel_coloring" / "__main__.py")],
    pathex=[str(source_root)],
    binaries=[],
    datas=[(str(resources), "pixel_coloring/resources")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=application_name,
    icon=str(resources / "icons/piksel-atolyesi.ico") if sys.platform == "win32" else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=application_name,
)
