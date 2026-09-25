FROM python:3.13-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libdbus-1-3 \
    libegl1 \
    libgl1 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .
RUN python3 -m venv /opt/piksel-build-venv \
    && /opt/piksel-build-venv/bin/python -m pip install --no-cache-dir . 'PyInstaller>=6.16,<7' \
    && PYTHON=/opt/piksel-build-venv/bin/python packaging/deb/build-deb.sh \
    && dpkg -i dist/piksel-atolyesi_*.deb \
    && QT_QPA_PLATFORM=offscreen piksel-atolyesi --smoke-test --data-dir /tmp/piksel-atolyesi-smoke
