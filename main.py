#!/usr/bin/env python3
# Linclear - universal uninstaller & system cleaner for Linux
import os

# --- MUST be set before any PyQt6 import -------------------------------
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.pop("QT_PLUGIN_PATH", None)
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)
# -----------------------------------------------------------------------

import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app import version
from app.ui.main_window import MainWindow


def resource_path(name: str) -> str:
    """Resolve a bundled data file (works from source and from PyInstaller)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        candidate = os.path.join(base, name)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(version.APP_NAME)
    app.setApplicationDisplayName(version.APP_NAME)
    app.setApplicationVersion(version.APP_VERSION)
    app.setOrganizationName(version.APP_NAME)
    app.setDesktopFileName("linclear")

    icon_file = resource_path("linclear.svg")
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())