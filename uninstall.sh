#!/usr/bin/env sh
# Remove the per-user installation. Saved paintings and progress are preserved
# unless --purge-data is explicitly supplied.
set -eu
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
APPLICATIONS_DIR="$DATA_HOME/applications"
ICON_THEME_DIR="$DATA_HOME/icons/hicolor"

if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--purge-data" ]; }; then
    printf '%s\n' "Usage: sh uninstall.sh [--purge-data]" >&2
    exit 2
fi

rm -f -- "$HOME/.local/bin/piksel-atolyesi"
rm -f -- "$APPLICATIONS_DIR/piksel-atolyesi.desktop"
rm -f -- "$ICON_THEME_DIR/512x512/apps/piksel-atolyesi.png"

if [ "${1:-}" = "--purge-data" ]; then
    rm -rf -- "$DATA_HOME/PixelColoring/PikselAtolyesi"
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t "$ICON_THEME_DIR" || true
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 --noincremental || true
fi

if [ "${1:-}" = "--purge-data" ]; then
    printf '%s\n' 'Piksel Atölyesi and its local data were removed.'
else
    printf '%s\n' 'Piksel Atölyesi was removed. Local progress was preserved.'
fi
