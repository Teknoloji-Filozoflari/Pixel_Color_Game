#!/usr/bin/env sh
# Build a self-contained AppImage after installing the project and PyInstaller.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$ROOT"
PYTHON=${PYTHON:-python3}
APPIMAGETOOL=${APPIMAGETOOL:-appimagetool}
APPIMAGE_RUNTIME=${APPIMAGE_RUNTIME:-}
ARCH_INPUT=${ARCH:-$(uname -m)}

case "$ARCH_INPUT" in
    x86_64|amd64) APPIMAGE_ARCH=x86_64 ;;
    aarch64|arm64) APPIMAGE_ARCH=aarch64 ;;
    *)
        printf '%s\n' "Unsupported AppImage architecture: $ARCH_INPUT" >&2
        exit 1
        ;;
esac

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    printf '%s\n' "Python was not found: $PYTHON" >&2
    exit 1
fi
if ! command -v "$APPIMAGETOOL" >/dev/null 2>&1 && [ ! -x "$APPIMAGETOOL" ]; then
    printf '%s\n' "appimagetool was not found: $APPIMAGETOOL" >&2
    exit 1
fi

VERSION=$(
    "$PYTHON" -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])'
)
PYI_WORK="$ROOT/build/pyinstaller"
PYI_DIST="$ROOT/build/pyinstaller-dist"
APPDIR="$ROOT/build/PikselAtolyesi.AppDir"
OUTPUT_DIR="$ROOT/dist"
OUTPUT="$OUTPUT_DIR/Piksel-Atolyesi-$VERSION-$APPIMAGE_ARCH.AppImage"

rm -rf "$PYI_WORK" "$PYI_DIST" "$APPDIR"
mkdir -p "$PYI_WORK" "$PYI_DIST" "$OUTPUT_DIR"

"$PYTHON" -m PyInstaller \
    --noconfirm \
    --clean \
    --workpath "$PYI_WORK" \
    --distpath "$PYI_DIST" \
    "$ROOT/packaging/appimage/piksel-atolyesi.spec"

mkdir -p \
    "$APPDIR/usr/lib" \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/doc/piksel-atolyesi" \
    "$APPDIR/usr/share/icons/hicolor/512x512/apps" \
    "$APPDIR/usr/share/metainfo"
cp -a "$PYI_DIST/piksel-atolyesi" "$APPDIR/usr/lib/piksel-atolyesi"
install -m 0755 "$ROOT/packaging/appimage/AppRun" "$APPDIR/AppRun"
install -m 0644 "$ROOT/packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.desktop" \
    "$APPDIR/io.github.teknolojifilozoflari.PixelColorGame.desktop"
install -m 0644 "$ROOT/packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.desktop" \
    "$APPDIR/usr/share/applications/io.github.teknolojifilozoflari.PixelColorGame.desktop"
install -m 0644 "$ROOT/src/pixel_coloring/resources/icons/piksel-atolyesi.png" \
    "$APPDIR/piksel-atolyesi.png"
install -m 0644 "$ROOT/src/pixel_coloring/resources/icons/piksel-atolyesi.png" \
    "$APPDIR/usr/share/icons/hicolor/512x512/apps/piksel-atolyesi.png"
install -m 0644 "$ROOT/packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml" \
    "$APPDIR/usr/share/metainfo/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml"
ln -s piksel-atolyesi.png "$APPDIR/.DirIcon"
cp "$ROOT/LICENSE" "$ROOT/THIRD_PARTY.md" "$ROOT/ASSETS_LICENSE.md" \
    "$APPDIR/usr/share/doc/piksel-atolyesi/"
cp -a "$ROOT/LICENSES" "$APPDIR/usr/share/doc/piksel-atolyesi/LICENSES"

rm -f "$OUTPUT"
if [ -n "$APPIMAGE_RUNTIME" ]; then
    ARCH=$APPIMAGE_ARCH APPIMAGE_EXTRACT_AND_RUN=1 \
        "$APPIMAGETOOL" --runtime-file "$APPIMAGE_RUNTIME" "$APPDIR" "$OUTPUT"
else
    ARCH=$APPIMAGE_ARCH APPIMAGE_EXTRACT_AND_RUN=1 "$APPIMAGETOOL" "$APPDIR" "$OUTPUT"
fi
chmod 0755 "$OUTPUT"
printf '%s\n' "Created $OUTPUT"
