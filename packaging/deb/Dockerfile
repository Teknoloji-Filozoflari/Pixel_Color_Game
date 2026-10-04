FROM python:3.13-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates libegl1 libgl1 libglib2.0-0 libdbus-1-3 libfontconfig1 libx11-6 libx11-xcb1 libxcb1 libxkbcommon0 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libxcb-randr0 libxcb-render0 libxcb-shm0 libxcb-sync1 libxcb-xfixes0 libxcb-xinerama0 libxcb-xkb1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .
RUN python3 -m venv /opt/piksel-build-venv \
    && /opt/piksel-build-venv/bin/python -m pip install --no-cache-dir -c packaging/constraints-linux.txt '.[dev]' PyInstaller \
    && /opt/piksel-build-venv/bin/python -m ruff check src tests run.py packaging/build_bundle.py packaging/build_rpm.py \
    && /opt/piksel-build-venv/bin/python -m pytest -q \
    && PYTHON=/opt/piksel-build-venv/bin/python packaging/deb/build-deb.sh \
    && dpkg -i dist/piksel-atolyesi_*.deb \
    && QT_QPA_PLATFORM=offscreen piksel-atolyesi --smoke-test --data-dir /tmp/piksel-atolyesi-smoke
