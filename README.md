# Linclear

### Universal uninstaller and system cleaner for Linux

*One window. Every package. Any distribution.*

**v1.5.0** · MIT License · Shipped as a single AppImage

</div>

---

Linclear discovers **everything** installed on your machine — DEB, RPM, Pacman,
Snap, Flatpak, AppImage and manually installed `.desktop` entries — and lets
you remove it from one place, with a fast, modern dark UI.

No terminal gymnastics. No forgotten config folders. No `sudo apt remove` +
`sudo apt purge` + `rm -rf ~/.config/...` dance. Just pick what you want gone
and Linclear handles the rest — **showing you every command before it runs**.

---

## ✨ Features

| | |
|---|---|
| 🔍 **Real-time search** | Instant filtering across names, descriptions and categories |
| 🎯 **Source filter & sort** | Filter by DEB / RPM / Pacman / Snap / Flatpak / AppImage / Manual, sort by name, size or source |
| ☑️ **Multi-selection** | Ctrl+Click and Shift+Click for batch uninstall |
| 📋 **Detail panel** | Full package info — version, size, category, path, exact uninstall command |
| 📊 **Live log & progress** | Every command streams its output, every operation has a progress bar |
| 📦 **AppImage Finder** | Quick scan of common locations + deep `find` across `$HOME`, `/opt`, `/usr/local`, `/usr/share` |
| 🧹 **Leftover scanner** | Finds orphaned files in `~/.config`, `~/.local/share`, `~/.cache`, `~/.local/bin`, `/etc`, `/var/lib`, `/opt` + broken symlink detection |
| 🛡️ **Safety blacklist** | `systemd`, `glibc`, `bash`, `apt`, `dnf`, `pacman`, kernels, bootloaders… can never be removed |
| 🔐 **Smart privilege escalation** | `pkexec` first, terminal fallback (`gnome-terminal`, `konsole`, `xfce4-terminal`, `xterm`) |
| 👁️ **Transparency** | Every command is displayed **before** it runs — no hidden `sudo rm -rf` |

---

## 📦 Supported sources

| Source | Discovery | Removal |
|:------:|-----------|---------|
| **DEB** | `dpkg-query` | `apt-get remove` / `dpkg --purge` |
| **RPM** | `rpm -qa` | `dnf remove` / `rpm -e` |
| **Pacman** | `pacman -Qi` | `pacman -Rns` |
| **Snap** | `snap list` | `snap remove` |
| **Flatpak** | `flatpak list --app` | `flatpak uninstall` |
| **AppImage** | directory scan + deep `find` | `rm` (with elevation if needed) |
| **Manual** | `.desktop` files not package-owned | `rm` |

---

## 🐧 Distribution support

Linclear is built to work on every major Linux family out of the box:

| Family | Distributions | Backend |
|:------:|---------------|:-------:|
| 🟠 **Debian** | Debian, Ubuntu, Linux Mint, Pop!_OS, elementary, Zorin | DEB |
| 🔵 **Fedora** | Fedora, RHEL, CentOS Stream, AlmaLinux, Rocky | RPM |
| 🟣 **SUSE** | OpenSUSE Tumbleweed, OpenSUSE Leap, SLES | RPM |
| 🔷 **Arch** | Arch Linux, Manjaro, EndeavourOS, Garuda, CachyOS | Pacman |

Snap, Flatpak, AppImage and manually installed `.desktop` entries are supported
on **all of the above**, provided the corresponding tools are installed.

---

## 🛠️ Build from source

**Build requirements:**

- Python 3.11+
- `python3-venv`
  - Debian/Ubuntu: `sudo apt install python3-venv`
  - Fedora: `sudo dnf install python3`
  - Arch: `sudo pacman -S python`
- `curl` **or** `wget`
- `libfuse2` (only to test the resulting AppImage)

`linuxdeploy` and `linuxdeploy-plugin-qt` are downloaded automatically by the
build script.

```bash
cd linclear/
python3 -m venv .venv
source .venv/bin/activate
pip install PyQt6 pyinstaller
./build_appimage.sh
```
Result: Linclear-1.5.0-<arch>.AppImage in the project root.
# 🚀 Run
chmod +x Linclear-1.5.0-x86_64.AppImage
./Linclear-1.5.0-x86_64.AppImage
If it fails to launch — blank window, cannot load xcb plugin, or a
libfuse2 error — jump to Runtime dependencies
at the very bottom of this document.
📄 License

MIT — see LICENSE for the full text.
<br> <br> <br><div align="center">
⬇️ Runtime dependencies

Only needed if the AppImage refuses to launch.

An AppImage bundles Python, Qt and Linclear's own code — but not glibc,
the X11/xcb libraries, or libfuse2. Those must already be present on your
system.
</div>
🟠 Debian / Ubuntu / Linux Mint / Pop!_OS
bash

sudo apt update
sudo apt install -y \
    libfuse2 \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    libx11-xcb1 \
    libxrender1 \
    libxi6 \
    libxtst6 \
    libxfixes3 \
    libxrandr2 \
    libfontconfig1 \
    libfreetype6 \
    libglib2.0-0 \
    libdbus-1-3 \
    libgl1 \
    libegl1

🔵 Fedora / RHEL / CentOS Stream
bash

sudo dnf install -y \
    fuse-libs \
    xcb-util-cursor \
    xcb-util-wm \
    xcb-util-image \
    xcb-util-keysyms \
    xcb-util-renderutil \
    libxkbcommon \
    libxkbcommon-x11 \
    libX11-xcb \
    libXrender \
    libXi \
    libXtst \
    libXfixes \
    libXrandr \
    fontconfig \
    freetype \
    glib2 \
    dbus-libs \
    mesa-libGL \
    mesa-libEGL

🔷 Arch Linux / Manjaro / EndeavourOS
bash

sudo pacman -S --needed \
    fuse2 \
    xcb-util-cursor \
    xcb-util-wm \
    xcb-util-image \
    xcb-util-keysyms \
    xcb-util-renderutil \
    libxkbcommon \
    libxkbcommon-x11 \
    libx11 \
    libxrender \
    libxi \
    libxtst \
    libxfixes \
    libxrandr \
    fontconfig \
    freetype2 \
    glib2 \
    dbus \
    mesa \
    libglvnd

🟣 OpenSUSE Tumbleweed / Leap
bash

sudo zypper install -y \
    libfuse2 \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxkbcommon-x11-0 \
    libX11-xcb1 \
    libXrender1 \
    libXi6 \
    libXtst6 \
    fontconfig \
    freetype2 \
    glib2 \
    libdbus-1-3 \
    libGL1 \
    libEGL1

🔎 How to find exactly what is missing

If the AppImage refuses to launch, run it with Qt's plugin debug output:
bash

QT_DEBUG_PLUGINS=1 ./Linclear-1.5.0-x86_64.AppImage 2>&1 | head -60

Or extract it and inspect the binary directly:
bash

./Linclear-1.5.0-x86_64.AppImage --appimage-extract
cd squashfs-root
ldd usr/bin/linclear                    | grep "not found"
ldd usr/plugins/platforms/libqxcb.so    | grep "not found"

Every line printed as not found is a library you still need to install.
📦 Prefer a native package instead?

If you'd rather not install any dependencies manually, use a distribution
package — .deb, .rpm or .pkg.tar.zst. Those declare their dependencies
and your package manager pulls them in automatically.
<div align="center">

Linclear — because uninstalling software on Linux shouldn't require a manual.
</div> ```
