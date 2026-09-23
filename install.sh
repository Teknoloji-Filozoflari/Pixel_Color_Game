#!/usr/bin/env sh
# Run once from the extracted Linux package: sh install.sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
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
printf '%s\n' 'Installation complete. Start the game with: sh start.sh'
