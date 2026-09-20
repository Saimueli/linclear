from PyQt6.QtWidgets import QApplication

DARK_QSS = """
* { font-size: 10pt; }
QMainWindow, QWidget { background-color: #1e1f22; color: #e6e6e6; }
QToolBar { background: #26282c; border: 0; padding: 4px; spacing: 4px; }
QToolButton { padding: 6px 10px; border-radius: 6px; }
QToolButton:hover { background: #35383d; }
QLineEdit, QComboBox, QPlainTextEdit, QTextEdit, QListWidget, QTreeWidget {
    background: #2a2c30; border: 1px solid #3a3d42; border-radius: 6px; padding: 4px;
    selection-background-color: #4a6da7;
}
QLineEdit:focus, QComboBox:focus { border: 1px solid #5b8def; }
QListWidget::item { padding: 4px 6px; border-radius: 4px; }
QListWidget::item:selected { background: #3a5a99; }
QPushButton { background: #35383d; border: 1px solid #45484e; border-radius: 6px;
              padding: 6px 14px; }
QPushButton:hover { background: #3f4249; }
QPushButton#danger { background: #8a2b2b; border-color: #a03535; }
QPushButton#danger:hover { background: #a03535; }
QProgressBar { background: #2a2c30; border: 1px solid #3a3d42; border-radius: 6px;
               text-align: center; }
QProgressBar::chunk { background: #5b8def; border-radius: 5px; }
QGroupBox { border: 1px solid #3a3d42; border-radius: 6px; margin-top: 12px;
            padding-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px;
                   color: #9aa0a6; }
QLabel#title { font-size: 14pt; font-weight: 600; }
QLabel#subtitle { color: #9aa0a6; }
QSplitter::handle { background: #2a2c30; }
"""

LIGHT_QSS = """
* { font-size: 10pt; }
QMainWindow, QWidget { background-color: #f6f7f9; color: #1c1e21; }
QToolBar { background: #eceef1; border: 0; padding: 4px; spacing: 4px; }
QToolButton { padding: 6px 10px; border-radius: 6px; }
QToolButton:hover { background: #dcdfe3; }
QLineEdit, QComboBox, QPlainTextEdit, QTextEdit, QListWidget, QTreeWidget {
    background: #ffffff; border: 1px solid #c8ccd1; border-radius: 6px; padding: 4px;
    selection-background-color: #b3cdf5;
}
QListWidget::item { padding: 4px 6px; border-radius: 4px; }
QListWidget::item:selected { background: #cfe0fa; color: #1c1e21; }
QPushButton { background: #e6e8ec; border: 1px solid #c8ccd1; border-radius: 6px;
              padding: 6px 14px; }
QPushButton:hover { background: #dcdfe3; }
QPushButton#danger { background: #d9534f; border-color: #c9302c; color: white; }
QPushButton#danger:hover { background: #c9302c; }
QProgressBar { background: #ffffff; border: 1px solid #c8ccd1; border-radius: 6px;
               text-align: center; }
QProgressBar::chunk { background: #5b8def; border-radius: 5px; }
QGroupBox { border: 1px solid #c8ccd1; border-radius: 6px; margin-top: 12px;
            padding-top: 8px; }
QLabel#title { font-size: 14pt; font-weight: 600; }
QLabel#subtitle { color: #6b7280; }
"""


def apply_theme(app: QApplication, dark: bool = True):
    app.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)