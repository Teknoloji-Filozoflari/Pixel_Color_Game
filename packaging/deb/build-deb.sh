#!/bin/sh
# Build an amd64/arm64 Debian package on the target Debian or Pardus release.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$ROOT"
PYTHON=${PYTHON:-python3}
MAINTAINER=${MAINTAINER:-Teknoloji Filozofları <teknolojifilozoflari@users.noreply.github.com>}

for program in "$PYTHON" dpkg dpkg-deb; do
    if ! command -v "$program" >/dev/null 2>&1; then
        printf '%s\n' "Required program was not found: $program" >&2
        exit 1
    fi
done

ARCH=$(dpkg --print-architecture)
case "$ARCH" in
    amd64|arm64) ;;
    *)
        printf '%s\n' "Unsupported Debian architecture: $ARCH" >&2
        exit 1
        ;;
esac

VERSION=$(
    "$PYTHON" -c 'import pathlib, tomllib; print(tomllib.loads(pathlib.Path("pyproject.toml").read_text())["project"]["version"])'
)
PACKAGE_VERSION="$VERSION-1"
WORK="$ROOT/build/deb-pyinstaller"
DIST="$ROOT/build/deb-pyinstaller-dist"
STAGING="$ROOT/build/deb-staging"
OUTPUT="$ROOT/dist/piksel-atolyesi_${PACKAGE_VERSION}_${ARCH}.deb"

rm -rf "$WORK" "$DIST" "$STAGING"
mkdir -p "$WORK" "$DIST" "$STAGING/DEBIAN" \
    "$STAGING/usr/bin" \
    "$STAGING/usr/lib" \
    "$STAGING/usr/share/applications" \
    "$STAGING/usr/share/doc/piksel-atolyesi" \
    "$STAGING/usr/share/icons/hicolor/512x512/apps" \
    "$STAGING/usr/share/metainfo" \
    "$ROOT/dist"

"$PYTHON" -m PyInstaller \
    --noconfirm \
    --clean \
    --workpath "$WORK" \
    --distpath "$DIST" \
    "$ROOT/packaging/appimage/piksel-atolyesi.spec"

cp -a "$DIST/piksel-atolyesi" "$STAGING/usr/lib/piksel-atolyesi"
install -m 0755 "$ROOT/packaging/deb/piksel-atolyesi" "$STAGING/usr/bin/piksel-atolyesi"
install -m 0644 "$ROOT/packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.desktop" \
    "$STAGING/usr/share/applications/io.github.teknolojifilozoflari.PixelColorGame.desktop"
install -m 0644 "$ROOT/src/pixel_coloring/resources/icons/piksel-atolyesi.png" \
    "$STAGING/usr/share/icons/hicolor/512x512/apps/piksel-atolyesi.png"
install -m 0644 "$ROOT/packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml" \
    "$STAGING/usr/share/metainfo/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml"
cp "$ROOT/LICENSE" "$ROOT/THIRD_PARTY.md" "$ROOT/ASSETS_LICENSE.md" \
    "$STAGING/usr/share/doc/piksel-atolyesi/"
cp -a "$ROOT/LICENSES" "$STAGING/usr/share/doc/piksel-atolyesi/LICENSES"

INSTALLED_SIZE=$(du -sk "$STAGING/usr" | cut -f1)
cat > "$STAGING/DEBIAN/control" <<EOF
Package: piksel-atolyesi
Version: $PACKAGE_VERSION
Section: games
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Installed-Size: $INSTALLED_SIZE
Depends: libc6, libdbus-1-3, libegl1, libgl1, libxkbcommon-x11-0, libxcb-cursor0
Homepage: https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game
Description: Offline color-by-number game
 Piksel Atölyesi provides a collection of pixel paintings and lets users
 import images to create their own color-by-number games.
EOF

dpkg-deb --build --root-owner-group "$STAGING" "$OUTPUT"
printf '%s\n' "Created $OUTPUT"
