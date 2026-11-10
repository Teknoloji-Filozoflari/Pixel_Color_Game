import os
import sys
from pathlib import Path

project_root = Path(SPECPATH).parents[1]
source_root = project_root / 'src'
resources = source_root / 'pixel_coloring' / 'resources'
icns = os.environ.get('PIKSEL_MACOS_ICNS')
version = os.environ.get('PIKSEL_APP_VERSION', '0.0.0')

a = Analysis(
    [str(source_root / 'pixel_coloring' / '__main__.py')],
    pathex=[str(source_root)],
    binaries=[],
    datas=[(str(resources), 'pixel_coloring/resources')],
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
    name='Piksel Atölyesi',
    icon=icns,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Piksel Atölyesi',
)

app = BUNDLE(
    coll,
    name='Piksel Atölyesi.app',
    icon=icns,
    bundle_identifier='com.teknolojifilozoflari.pikselatolyesi',
    info_plist={
        'CFBundleDisplayName': 'Piksel Atölyesi',
        'CFBundleName': 'Piksel Atölyesi',
        'CFBundleShortVersionString': version,
        'CFBundleVersion': version,
        'NSHighResolutionCapable': True,
        'LSPrincipalClass': 'NSApplication',
        'NSSupportsAutomaticGraphicsSwitching': True,
    },
)
