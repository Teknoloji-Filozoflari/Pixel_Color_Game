#!/usr/bin/env sh
# Run once from the extracted Linux package: sh install.sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$PROJECT_DIR"
PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    printf '%s\n' 'Python 3.13+ is required. Install Python using your Linux package manager.' >&2
    exit 1
fi
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 13) else "Python 3.13+ is required.")'
if [ ! -x .venv/bin/python ]; then
    "$PYTHON" -m venv .venv
fi
.venv/bin/python -m pip install -e .

# Install a per-user launcher, icon and application-menu entry. No root access is
# needed. XDG_DATA_HOME is honoured for desktops using a non-default data path.
DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
BIN_HOME="$HOME/.local/bin"
APPLICATIONS_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/512x512/apps"
LAUNCHER="$BIN_HOME/piksel-atolyesi"
DESKTOP_FILE="$APPLICATIONS_DIR/piksel-atolyesi.desktop"

# Desktop Entry Exec quoting is cumbersome for paths containing spaces. Pointing
# at the conventional per-user bin directory keeps the generated entry portable.
case "$LAUNCHER" in
    *[!A-Za-z0-9_./-]*)
        printf '%s\n' "Cannot create a desktop entry for a path containing special characters: $LAUNCHER" >&2
        exit 1
        ;;
esac

mkdir -p "$BIN_HOME" "$APPLICATIONS_DIR" "$ICON_DIR"
ln -sfn "$PROJECT_DIR/.venv/bin/pixel-coloring" "$LAUNCHER"
install -m 0644 src/pixel_coloring/resources/icons/piksel-atolyesi.png \
    "$ICON_DIR/piksel-atolyesi.png"
sed "s|@EXEC@|$LAUNCHER|" packaging/linux/piksel-atolyesi.desktop.in > "$DESKTOP_FILE"
chmod 0644 "$DESKTOP_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q -t "$DATA_HOME/icons/hicolor" || true
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental || true
elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 --noincremental || true
fi

printf '%s\n' 'Installation complete.'
printf '%s\n' 'Open "Piksel Atölyesi" from the application menu or run: piksel-atolyesi'
