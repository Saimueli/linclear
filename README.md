# Linclear 🧹

A simple, fast, and lightweight system cleaner for Linux, written in Python. **Linclear** is designed to help you easily manage, detect, and clean application data across your system. It is optimized primarily for **Ubuntu**, **Fedora**, **Arch Linux**, **NixOS**, and their derivatives (Linux Mint, Pop!_OS, Nobara, Manjaro, EndeavourOS, etc.).

![Version](https://img.shields.io/badge/version-v1.2.4-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)

## ✨ Features (v1.2.4)

* **Multi-Format Application Detection:** Scans and identifies applications installed via:
  * **DEB** (Debian / Ubuntu package manager)
  * **RPM** (Fedora / RHEL package manager)
  * **Pacman** (Arch Linux / Manjaro / EndeavourOS)
  * **Nix** (NixOS and Nix profiles)
  * **Flatpak** packages
  * **Snap** packages
  * **AppImage** files (deep filesystem scan)
  * **Script-based / Manual installs** (custom binary paths and standalone scripts)
* **System Cleanup:** Quickly locate and remove unnecessary application files and residue.
* **AppImage Finder:** Deep-scan your system for AppImage files and remove them with one click.
* **Distro-Friendly:** Built from the ground up for Ubuntu/Debian, Fedora, Arch, and NixOS environments.

## 🚀 Installation & Usage (AppImage)

The easiest way to run Linclear is via the standalone **AppImage**. No installation or additional dependencies required!

1. Download the latest `.AppImage` from the [Releases](https://github.com/Saimueli/linclear/releases) section.
2. Grant execution permissions:
   * **GUI:** Right-click the `.AppImage` file -> **Properties** -> **Permissions** -> Check **"Allow executing file as program"**.
   * **Terminal:**
     ```bash
     chmod +x Linclear-1.2.4-x86_64.AppImage
     ```
3. Run the application by double-clicking it or via terminal:
   ```bash
   ./Linclear-1.2.4-x86_64.AppImage
   ```

> **Fedora users:** If you see an error about `libfuse.so.2`, either run `sudo dnf install -y fuse fuse-libs` or launch with `./Linclear-1.2.4-x86_64.AppImage --appimage-extract-and-run`.
