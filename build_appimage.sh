#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

APP_NAME="Linclear"
VERSION="1.4.0"
ARCH="$(uname -m)"
OUT="${APP_NAME}-${VERSION}-${ARCH}.AppImage"

echo "==> Building ${APP_NAME} ${VERSION} for ${ARCH}"

for f in main.py linclear.spec linclear.desktop linclear.svg AppRun requirements.txt; do
    if [ ! -f "$f" ]; then
        echo "ERROR: required file '$f' is missing in $HERE" >&2
        exit 1
    fi
done

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is required." >&2
    exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
    echo "ERROR: python3-venv is not installed." >&2
    echo "  Debian/Ubuntu: sudo apt install python3-venv" >&2
    echo "  Fedora:        sudo dnf install python3" >&2
    echo "  Arch:          sudo pacman -S python" >&2
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "==> Creating virtualenv (.venv)"
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source ".venv/bin/activate"

python -m pip install --upgrade pip wheel >/dev/null
python -m pip install -r requirements.txt pyinstaller

rm -rf build dist AppDir "${OUT}"

echo "==> Running PyInstaller"
pyinstaller --noconfirm --clean linclear.spec

mkdir -p tools

fetch() {
    local url="$1" out="$2"
    if [ -f "$out" ]; then
        return 0
    fi
    echo "==> Downloading $(basename "$out")"
    if command -v curl >/dev/null 2>&1; then
        curl -L --fail --retry 3 -o "$out" "$url"
    elif command -v wget >/dev/null 2>&1; then
        wget -O "$out" "$url"
    else
        echo "ERROR: curl or wget is required." >&2
        exit 1
    fi
    chmod +x "$out"
}

LD="$HERE/tools/linuxdeploy-${ARCH}.AppImage"
LDQT="$HERE/tools/linuxdeploy-plugin-qt-${ARCH}.AppImage"

fetch "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${ARCH}.AppImage" "$LD"
fetch "https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-${ARCH}.AppImage" "$LDQT"

ln -sf "linuxdeploy-plugin-qt-${ARCH}.AppImage" "$HERE/tools/linuxdeploy-plugin-qt" || true

export APPIMAGE_EXTRACT_AND_RUN=1
export PATH="$HERE/tools:$PATH"

echo "==> Assembling AppDir"
rm -rf AppDir
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/scalable/apps

cp -a dist/linclear/. AppDir/usr/bin/
cp linclear.desktop AppDir/usr/share/applications/
cp linclear.svg     AppDir/usr/share/icons/hicolor/scalable/apps/
cp linclear.desktop AppDir/
cp linclear.svg     AppDir/
cp AppRun           AppDir/AppRun

chmod +x AppDir/AppRun
chmod +x AppDir/usr/bin/linclear

echo "==> Running linuxdeploy"
if ! "$LD" --appdir AppDir --plugin qt --output appimage; then
    echo "==> linuxdeploy (with Qt plugin) failed - retrying without it"
    "$LD" --appdir AppDir --output appimage
fi

shopt -s nullglob
for f in *.AppImage; do
    if [ "$f" != "$OUT" ]; then
        mv -f "$f" "$OUT"
    fi
done
shopt -u nullglob

echo
echo "==> DONE:  $HERE/$OUT"
echo "    Run:  ./$OUT"
