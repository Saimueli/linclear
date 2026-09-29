# Linclear

**Universal uninstaller and system cleaner for Linux — shipped as a single AppImage.**

Linclear discovers *everything* installed on your machine and lets you remove it
from one place, with a fast, modern dark UI.

Current version: **1.4.0**

## Supported sources

| Source     | Discovery                          | Removal                          |
|------------|------------------------------------|----------------------------------|
| DEB        | `dpkg-query`                       | `apt-get remove` / `dpkg --purge`|
| RPM        | `rpm -qa`                          | `dnf remove` / `rpm -e`          |
| Pacman     | `pacman -Qi`                       | `pacman -Rns`                    |
| Snap       | `snap list`                        | `snap remove`                    |
| Flatpak    | `flatpak list --app`               | `flatpak uninstall`              |
| AppImage   | directory scan + deep `find`       | `rm` (with elevation if needed)  |
| Manual     | `.desktop` files not package-owned | `rm`                             |

## Features

- Real-time search, source filter, sort by name / size / source
- Multi-selection (Ctrl+Click, Shift+Click) for batch uninstall
- Detail panel with full package information
- Log panel + progress bar for every operation
- **AppImage Finder** with a deep scan of `$HOME`, `/opt`, `/usr/local`, `/usr/share`
- **Leftover scanner** for `~/.config`, `~/.local/share`, `~/.cache`,
  `~/.local/bin`, `/etc`, `/var/lib`, `/opt` + broken symlink detection
- Safety blacklist — system-critical packages can never be removed
- Privilege escalation via `pkexec`, with a terminal fallback
  (`gnome-terminal`, `konsole`, `xfce4-terminal`, `xterm`)
- Every command is shown to you **before** it runs

## Requirements

- Python 3.11+
- PyQt6
- `linuxdeploy` + `linuxdeploy-plugin-qt` (downloaded automatically by the build script)
- `curl` **or** `wget`

## Build

```bash
cd linclear/
python3 -m venv .venv
source .venv/bin/activate
pip install PyQt6 pyinstaller
./build_appimage.sh
