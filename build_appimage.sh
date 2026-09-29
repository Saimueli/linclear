#!/usr/bin/env bash
# Build Linclear-<version>-<arch>.AppImage
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

APP_NAME="Linclear"
VERSION="1.4.0"
ARCH="$(uname -m)"
OUT="${APP_NAME}-${VERSION}-${ARCH}.AppImage"

echo "==> Building ${APP_NAME} ${VERSION} for ${ARCH}"

# ------------------------------------------------------------------ venv
if [ ! -d ".venv" ]; then
    echo "==> Creating virtualenv (.venv)"
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source ".venv/bin/activate"

python -m pip install --upgrade pip wheel >/dev/null
python -m pip install -r requirements.txt pyinstaller

# ------------------------------------------------------------------ clean
rm -rf build dist AppDir "${OUT}"

# ------------------------------------------------------------------ pyinstaller
echo "==> Running PyInstaller"
pyinstaller --noconfirm --clean linclear.spec

# ------------------------------------------------------------------ tools
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

# linuxdeploy looks the plugin up by the name "linuxdeploy-plugin-qt" on PATH
ln -sf "linuxdeploy-plugin-qt-${ARCH}.AppImage" "$HERE/tools/linuxdeploy-plugin-qt"
chmod +x "$HERE/tools/linuxdeploy-plugin-qt" || true

export APPIMAGE_EXTRACT_AND_RUN=1
export PATH="$HERE/tools:$PATH"

# ------------------------------------------------------------------ AppDir
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

# ------------------------------------------------------------------ linuxdeploy
echo "==> Running linuxdeploy"
if ! "$LD" --appdir AppDir --plugin qt --output appimage; then
    echo "==> linuxdeploy (with Qt plugin) failed - retrying without it"
    "$LD" --appdir AppDir --output appimage
fi

# ------------------------------------------------------------------ rename
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