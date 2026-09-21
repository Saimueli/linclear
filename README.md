# Linclear 🧹

A simple, fast, and lightweight system cleaner for Linux, written in Python. **Linclear** is designed to help you easily manage, detect, and clean application data across your system. It is optimized primarily for **Ubuntu**, **Fedora**, and their derivatives (Linux Mint, Pop!_OS, Nobara, etc.).

![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)

## ✨ Features (v1.1.0)

* **Multi-Format Application Detection:** Scans and identifies applications installed via:
  * **DEB** (Debian / Ubuntu package manager)
  * **RPM** (Fedora / RHEL package manager)
  * **Flatpak** packages
  * **Snap** packages
  * **Script-based / Manual installs** (custom binary paths and standalone scripts)
* **System Cleanup:** Quickly locate and remove unnecessary application files and residue.
* **Distro-Friendly:** Built from the ground up for Ubuntu/Debian and Fedora-based environments.

## 🚀 Installation & Usage (AppImage)

The easiest way to run Linclear is via the standalone **AppImage**. No installation or additional dependencies required!

1. Download the latest `.AppImage` from the [Releases](https://github.com/YOUR-USERNAME/linclear/releases) section.
2. Grant execution permissions:
   * **GUI:** Right-click the `.AppImage` file -> **Properties** -> **Permissions** -> Check **"Allow executing file as program"**.
   * **Terminal:**
     ```bash
     chmod +x Linclear-v1.0.0-x86_64.AppImage
     ```
3. Run the application by double-clicking it or via terminal:
   ```bash
   ./Linclear-v1.0.0-x86_64.AppImage
