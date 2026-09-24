from pathlib import Path


project_root = Path(SPECPATH).parents[1]
source_root = project_root / "src"
resources = source_root / "pixel_coloring" / "resources"

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
    name="piksel-atolyesi",
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
    name="piksel-atolyesi",
)
