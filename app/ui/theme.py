"""Dark / light stylesheets and per-source badge colours."""

SOURCE_COLORS = {
    "DEB": "#8a2b2b",
    "RPM": "#b35a2a",
    "Pacman": "#1f8a9e",
    "Snap": "#7a5a33",
    "Flatpak": "#3a6fd8",
    "AppImage": "#7a3ad8",
    "Manual": "#2f8a4a",
}

DEFAULT_SOURCE_COLOR = "#5a5f66"

DARK_QSS = """
QWidget {
    background-color: #1e1f22;
    color: #e6e6e6;
    font-size: 10pt;
}
QMainWindow, QDialog { background-color: #1e1f22; }

QToolBar {
    background: #26282c;
    border: none;
    padding: 4px;
    spacing: 4px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e6e6e6;
}
QToolButton:hover { background: #33363b; }
QToolButton:pressed { background: #3d4046; }
QToolButton:disabled { color: #6b7075; }

QLineEdit, QComboBox, QSpinBox {
    background: #2a2c30;
    border: 1px solid #3a3d42;
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: #5b8def;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #5b8def; }
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background: #2a2c30;
    border: 1px solid #3a3d42;
    selection-background-color: #5b8def;
    outline: none;
}

QListWidget {
    background: #232529;
    border: 1px solid #2f3237;
    border-radius: 8px;
    outline: none;
    padding: 2px;
}

QPlainTextEdit, QTextEdit, QTextBrowser {
    background: #1a1b1e;
    border: 1px solid #2f3237;
    border-radius: 8px;
    font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
    font-size: 9pt;
    color: #cfd3d8;
    padding: 4px;
}

QPushButton {
    background: #2f3237;
    border: 1px solid #3a3d42;
    border-radius: 6px;
    padding: 6px 14px;
    color: #e6e6e6;
}
QPushButton:hover { background: #3a3d42; }
QPushButton:pressed { background: #45484f; }
QPushButton:disabled { color: #6b7075; }
QPushButton#danger { background: #8a2b2b; border-color: #a33333; }
QPushButton#danger:hover { background: #a03333; }

QProgressBar {
    background: #2a2c30;
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
}
QProgressBar::chunk { background: #5b8def; border-radius: 5px; }

QSplitter::handle { background: #2a2c30; }
QSplitter::handle:horizontal { width: 4px; }

QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #3a3d42; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #4a4e55; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #3a3d42; border-radius: 5px; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: #4a4e55; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QCheckBox::indicator {
    width: 15px; height: 15px;
    border-radius: 3px;
    border: 1px solid #4a4e55;
    background: #2a2c30;
}
QCheckBox::indicator:checked { background: #5b8def; border-color: #5b8def; }

QLabel#title { font-size: 13pt; font-weight: 600; }
QLabel#subtitle { color: #9aa0a6; }

QStatusBar { background: #26282c; color: #9aa0a6; }
QStatusBar::item { border: none; }

QMessageBox { background: #24262a; }
QToolTip {
    background: #2a2c30;
    color: #e6e6e6;
    border: 1px solid #3a3d42;
    padding: 4px;
}
"""

LIGHT_QSS = """
QWidget {
    background-color: #f4f5f7;
    color: #1e1f22;
    font-size: 10pt;
}
QMainWindow, QDialog { background-color: #f4f5f7; }

QToolBar { background: #ffffff; border: none; padding: 4px; spacing: 4px; }
QToolButton {
    background: transparent; border: 1px solid transparent;
    border-radius: 6px; padding: 6px 10px;
}
QToolButton:hover { background: #e6e8eb; }
QToolButton:pressed { background: #d8dce2; }

QLineEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: #5b8def;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #5b8def; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d0d4da;
    selection-background-color: #5b8def;
    selection-color: #ffffff;
    outline: none;
}

QListWidget {
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 8px;
    outline: none;
    padding: 2px;
}

QPlainTextEdit, QTextEdit, QTextBrowser {
    background: #ffffff;
    border: 1px solid #d0d4da;
    border-radius: 8px;
    font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
    font-size: 9pt;
    padding: 4px;
}

QPushButton {
    background: #e9ebef;
    border: 1px solid #d0d4da;
    border-radius: 6px;
    padding: 6px 14px;
}
QPushButton:hover { background: #dfe2e7; }
QPushButton#danger { background: #8a2b2b; border-color: #a33333; color: #ffffff; }
QPushButton#danger:hover { background: #a03333; }

QProgressBar { background: #e0e3e8; border: none; border-radius: 5px; height: 10px; }
QProgressBar::chunk { background: #5b8def; border-radius: 5px; }

QSplitter::handle { background: #e0e3e8; }

QStatusBar { background: #ffffff; color: #6b7075; }
"""


def get_qss(light: bool) -> str:
    return LIGHT_QSS if light else DARK_QSS