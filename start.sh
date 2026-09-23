#!/usr/bin/env sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python run.py "$@"
fi
PYTHON=${PYTHON:-python3}
if ! "$PYTHON" -c 'import sys; assert sys.version_info >= (3, 13); import PySide6.QtWidgets, numpy, PIL' >/dev/null 2>&1; then
  printf '%s\n' 'First install the dependencies with: sh install.sh' >&2
  exit 1
fi
exec "$PYTHON" run.py "$@"
