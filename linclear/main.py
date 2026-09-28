#!/usr/bin/env python3
import sys
import os

if "APPDIR" in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from linclear.ui.main_window import MainWindow
from linclear.ui.theme import apply_theme


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Linclear")
    app.setApplicationDisplayName("Linclear")
    app.setOrganizationName("Linclear")
    apply_theme(app, dark=True)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
