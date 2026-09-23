from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QProgressBar, QMessageBox, QFileDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..backends.appimage import AppImageBackend
from ..models import human_size


class DeepScanWorker(QThread):
    output = pyqtSignal(str)
    done   = pyqtSignal(list)

    def run(self):
        try:
            items = AppImageBackend().deep_scan(emit=self.output.emit)
        except Exception as e:
            self.output.emit(f"[error] {e}")
            items = []
        self.done.emit(items)


class AppImageFinderDialog(QDialog):
    """Deep-scans the system for AppImages and lets the user remove them."""

    def __init__(self, parent=None, dry_run=False):
        super().__init__(parent)
        self.dry_run = dry_run
        self.setWindowTitle("Linclear — AppImage Finder")
        self.resize(860, 560)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "<b>Scanning for AppImage files…</b><br>"
            "Searches your home directory, /opt, /usr/local, and /usr/share "
            "up to depth 6."))

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list.itemChanged.connect(lambda _: self._update_summary())
        layout.addWidget(self.list, 1)

        self.summary = QLabel("Scanning…")
        layout.addWidget(self.summary)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

        btns = QHBoxLayout()
        self.add_btn = QPushButton("Add Manually…")
        self.add_btn.clicked.connect(self._add_manual)
        btns.addWidget(self.add_btn)
        btns.addStretch(1)
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("danger")
        self.delete_btn.clicked.connect(self._delete_selected)
        btns.addWidget(self.delete_btn)
        close = QPushButton("Close")
        close.clicked.connect(self.reject)
        btns.addWidget(close)
        layout.addLayout(btns)

        self._worker = DeepScanWorker()
        self._worker.output.connect(self._log)
        self._worker.done.connect(self._populate)
        self._worker.start()

    def _log(self, msg):
        parent = self.parent()
        if parent and hasattr(parent, "log"):
            parent.log(msg)

    def _populate(self, apps):
        self.progress.setVisible(False)
        self.list.clear()
        if not apps:
            self.summary.setText("No AppImages found.")
            return
        for a in apps:
            label = f"{a.name}   ·   {a.install_path}   ·   {a.size_human}"
            item = QListWidgetItem(label)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, a)
            self.list.addItem(item)
        self.summary.setText(f"{len(apps)} AppImage(s) found")
        self._update_summary()

    def _add_manual(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select AppImage files", str(Path.home()),
            "AppImages (*.AppImage *.appimage);;All files (*)")
        if not paths:
            return
        from pathlib import Path as _P
        for p in paths:
            a = AppImageBackend()._make_app(_P(p))
            item = QListWidgetItem(f"{a.name}   ·   {a.install_path}   ·   {a.size_human}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, a)
            self.list.addItem(item)
        self._update_summary()

    def _update_summary(self):
        n, total = 0, 0
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                n += 1
                total += it.data(Qt.ItemDataRole.UserRole).size_bytes
        self.summary.setText(f"{n} selected — {human_size(total)}")

    def _delete_selected(self):
        selected = [
            self.list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.list.count())
            if self.list.item(i).checkState() == Qt.CheckState.Checked
        ]
        if not selected:
            QMessageBox.information(self, "Linclear", "Nothing selected.")
            return
        if not self.dry_run:
            preview = "\n".join(f"  • {a.install_path}" for a in selected[:15])
            if len(selected) > 15:
                preview += f"\n  … and {len(selected) - 15} more"
            if QMessageBox.question(
                self, "Delete AppImages",
                f"Permanently delete {len(selected)} file(s)?\n\n{preview}"
            ) != QMessageBox.StandardButton.Yes:
                return

        from ..privileged import run_command
        import os
        from pathlib import Path as _P
        parent = self.parent()
        log = parent.log if parent and hasattr(parent, "log") else (lambda s: None)
        for a in selected:
            needs_root = not a.install_path.startswith(str(_P.home()))
            log(f"[appimage] removing {a.install_path}")
            run_command(["rm", "-rf", "--", a.install_path],
                        emit=log, privileged=needs_root, dry_run=self.dry_run)
        QMessageBox.information(self, "Linclear",
                                "Done — see log for details.")
        self.accept()