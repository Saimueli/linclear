"""Dialog for reviewing and removing leftover files."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QMessageBox, QPlainTextEdit, QProgressBar,
)

from .. import cleanup
from ..workers import FunctionWorker


class LeftoversDialog(QDialog):
    def __init__(self, apps, parent=None):
        super().__init__(parent)
        self.apps = list(apps)
        self.setWindowTitle("Leftover files")
        self.resize(780, 560)

        self._scan_worker = None
        self._remove_worker = None

        self._build_ui()
        self.scan()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Leftover files")
        title.setObjectName("title")
        layout.addWidget(title)

        names = ", ".join(a.name for a in self.apps) or "—"
        subtitle = QLabel(f"Searching files left behind by: {names}")
        subtitle.setObjectName("subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.list_widget = QListWidget()
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
        btn_all = QPushButton("Select all")
        btn_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        buttons.addWidget(btn_all)

        btn_none = QPushButton("Select none")
        btn_none.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        buttons.addWidget(btn_none)

        buttons.addStretch(1)

        self.btn_delete = QPushButton("Delete selected")
        self.btn_delete.setObjectName("danger")
        self.btn_delete.clicked.connect(self._on_delete)
        buttons.addWidget(self.btn_delete)

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        buttons.addWidget(btn_close)

        layout.addLayout(buttons)

    def _set_all(self, state):
        for index in range(self.list_widget.count()):
            self.list_widget.item(index).setCheckState(state)

    def log(self, text: str):
        if text is None:
            return
        self.log_view.appendPlainText(str(text))

    # ------------------------------------------------------------------ scan

    def scan(self):
        self.list_widget.clear()
        self.progress.setRange(0, 0)
        self.log("Scanning for leftovers…")

        worker = FunctionWorker(cleanup.find_leftovers, self.apps)
        worker.done.connect(self._on_scan_done)
        worker.failed.connect(self._on_scan_failed)
        worker.finished.connect(worker.deleteLater)
        self._scan_worker = worker
        worker.start()

    def _on_scan_done(self, items):
        items = list(items or [])
        items.extend(cleanup.find_broken_symlinks())

        for leftover in items:
            suffix = "  [root]" if leftover.needs_root else ""
            text = f"{leftover.path}   ({leftover.kind}, {leftover.size_str}){suffix}"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Unchecked if leftover.needs_root else Qt.CheckState.Checked
            )
            item.setData(Qt.ItemDataRole.UserRole, leftover)
            self.list_widget.addItem(item)

        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.log(f"Found {len(items)} candidate(s).")

    def _on_scan_failed(self, message):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.log(f"Scan failed: {message}")

    # ------------------------------------------------------------------ delete

    def _selected(self):
        selected = []
        for index in range(self.list_widget.count()):
            item = self.list_widget.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                selected.append(item.data(Qt.ItemDataRole.UserRole))
        return selected

    def _on_delete(self):
        items = self._selected()
        if not items:
            QMessageBox.information(self, "Delete", "Nothing is selected.")
            return

        preview = "\n".join(i.path for i in items[:20])
        if len(items) > 20:
            preview += f"\n… and {len(items) - 20} more"

        answer = QMessageBox.question(
            self, "Confirm deletion",
            f"{len(items)} item(s) will be permanently deleted:\n\n{preview}\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.progress.setRange(0, 0)
        self.btn_delete.setEnabled(False)

        worker = FunctionWorker(cleanup.remove_items, items)
        worker.done.connect(self._on_removed)
        worker.failed.connect(self._on_remove_failed)
        worker.finished.connect(worker.deleteLater)
        self._remove_worker = worker
        worker.start()

    def _on_removed(self, log_lines):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.btn_delete.setEnabled(True)
        for line in log_lines or []:
            self.log(line)
        self.scan()

    def _on_remove_failed(self, message):
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.btn_delete.setEnabled(True)
        self.log(f"Removal failed: {message}")