"""AppImage Finder dialog."""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QFileDialog, QMessageBox, QPlainTextEdit, QProgressBar,
)

from .. import backends, privileged
from ..models import human_size
from ..workers import FunctionWorker, CommandWorker


class AppImageDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AppImage Finder")
        self.resize(780, 540)

        self.changed = False
        self._scan_worker = None
        self._cmd_worker = None
        self._delete_queue = []

        self._build_ui()
        self.scan(deep=False)

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("AppImage files found on this system")
        title.setObjectName("title")
        layout.addWidget(title)

        hint = QLabel(
            "Quick scan covers the usual locations. Deep scan walks your home "
            "directory, /opt, /usr/local and /usr/share up to 6 levels."
        )
        hint.setObjectName("subtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget, 1)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(110)
        layout.addWidget(self.log_view)

        buttons = QHBoxLayout()
        self.btn_deep = QPushButton("Deep scan")
        self.btn_deep.clicked.connect(lambda: self.scan(deep=True))
        buttons.addWidget(self.btn_deep)

        self.btn_add = QPushButton("Add file…")
        self.btn_add.clicked.connect(self._on_add)
        buttons.addWidget(self.btn_add)

        buttons.addStretch(1)

        self.btn_delete = QPushButton("Delete selected")
        self.btn_delete.setObjectName("danger")
        self.btn_delete.clicked.connect(self._on_delete)
        buttons.addWidget(self.btn_delete)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        buttons.addWidget(self.btn_close)

        layout.addLayout(buttons)

    # ------------------------------------------------------------------ log

    def log(self, text: str):
        if text is None:
            return
        self.log_view.appendPlainText(str(text))

    # ------------------------------------------------------------------ scan

    def scan(self, deep: bool = False):
        self.list_widget.clear()
        self.progress.setRange(0, 0)
        self.log("Scanning for AppImages…" if not deep else "Deep scanning…")

        fn = backends.find_appimages_deep if deep else None

        if fn is None:
            self._on_scan_done(backends.find_appimages_deep.__wrapped__
                               if hasattr(backends.find_appimages_deep, "__wrapped__") else None)
            return

        worker = FunctionWorker(fn)
        worker.done.connect(self._on_scan_done)
        worker.failed.connect(self._on_scan_failed)
        worker.finished.connect(worker.deleteLater)
        self._scan_worker = worker
        worker.start()

    def _on_scan_done(self, paths):
        if paths is None:
            paths = []
        self.progress.setRange(0, 100)
        self.progress.setValue(100)

        for path in paths:
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            item = QListWidgetItem(f"{path}    [{human_size(size)}]")
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.list_widget.addItem(item)

        self.log(f"Found {len(paths)} AppImage file(s).")

    def _on_scan_failed(self, message):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.log(f"Scan failed: {message}")

    # ------------------------------------------------------------------ add

    def _on_add(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select an AppImage", os.path.expanduser("~"),
            "AppImage files (*.AppImage *.appimage);;All files (*)",
        )
        if not path:
            return
        self.changed = True
        try:
            size = os.path.getsize(path)
        except OSError:
            size = 0
        item = QListWidgetItem(f"{path}    [{human_size(size)}]")
        item.setData(Qt.ItemDataRole.UserRole, path)
        self.list_widget.addItem(item)
        self.log(f"Added {path}")

    # ------------------------------------------------------------------ delete

    def _on_delete(self):
        items = self.list_widget.selectedItems()
        if not items:
            QMessageBox.information(self, "Delete", "Select one or more files first.")
            return

        paths = [it.data(Qt.ItemDataRole.UserRole) for it in items]
        preview = "\n".join(paths)
        answer = QMessageBox.question(
            self, "Confirm deletion",
            "The following files will be deleted:\n\n" + preview + "\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._delete_queue = list(paths)
        self.progress.setRange(0, len(paths))
        self.progress.setValue(0)
        self._run_delete_next()

    def _run_delete_next(self):
        if not self._delete_queue:
            self.changed = True
            self.log("Deletion finished.")
            self.scan(deep=False)
            return

        path = self._delete_queue.pop(0)
        needs_root = path.startswith("/opt") or path.startswith("/usr")
        cmd = privileged.effective_command(["rm", "-f", path], needs_root)
        if cmd is None:
            self.log(f"cannot remove {path}: no pkexec or terminal available")
            self._run_delete_next()
            return

        self.log("$ " + privileged.display(cmd))
        worker = CommandWorker(cmd)
        worker.line.connect(self.log)
        worker.finished_rc.connect(self._on_delete_rc)
        worker.finished.connect(worker.deleteLater)
        self._cmd_worker = worker
        worker.start()

    def _on_delete_rc(self, rc: int):
        self.progress.setValue(min(self.progress.value() + 1, self.progress.maximum()))
        if rc != 0:
            self.log(f"exit code: {rc}")
        self._run_delete_next()