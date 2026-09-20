from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QListWidgetItem, QPushButton,
                             QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt
from ..models import human_size
from ..cleanup import remove_leftover


class LeftoversDialog(QDialog):
    def __init__(self, app, items, parent=None, dry_run=False):
        super().__init__(parent)
        self.app = app
        self.items = items
        self.dry_run = dry_run
        self.setWindowTitle(f"Linclear — Leftovers for {app.name}")
        self.resize(780, 520)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Leftover items found for '{app.name}':</b>"))
        layout.addWidget(QLabel(
            "Uncheck items you want to keep. System paths need root (pkexec)."))

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list.itemChanged.connect(lambda _: self._update_summary())
        for it in items:
            label = f"[{it.category}] {it.path}  ({it.size_human}) — {it.reason}"
            lw = QListWidgetItem(label)
            lw.setFlags(lw.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            lw.setCheckState(Qt.CheckState.Checked if it.selected
                             else Qt.CheckState.Unchecked)
            lw.setData(Qt.ItemDataRole.UserRole, it)
            self.list.addItem(lw)
        layout.addWidget(self.list, 1)

        self.summary = QLabel()
        layout.addWidget(self.summary)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self.clean_btn = QPushButton("Clean Selected")
        self.clean_btn.setObjectName("danger")
        self.clean_btn.clicked.connect(self.clean)
        btns.addWidget(self.clean_btn)
        close = QPushButton("Close")
        close.clicked.connect(self.reject)
        btns.addWidget(close)
        layout.addLayout(btns)

        self._update_summary()

    def _update_summary(self):
        total, n = 0, 0
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.checkState() == Qt.CheckState.Checked:
                n += 1
                total += it.data(Qt.ItemDataRole.UserRole).size_bytes
        self.summary.setText(f"{n} item(s) selected — total {human_size(total)}")

    def clean(self):
        selected = [
            self.list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.list.count())
            if self.list.item(i).checkState() == Qt.CheckState.Checked
        ]
        if not selected:
            QMessageBox.information(self, "Linclear", "No items selected.")
            return
        if not self.dry_run:
            preview = "\n".join(f"  • {i.path}" for i in selected[:15])
            if len(selected) > 15:
                preview += f"\n  … and {len(selected) - 15} more"
            if QMessageBox.question(
                self, "Confirm cleanup",
                f"Permanently delete {len(selected)} item(s)?\n\n{preview}"
            ) != QMessageBox.StandardButton.Yes:
                return

        log = getattr(self.parent(), "log", lambda s: None)
        self.clean_btn.setEnabled(False)
        n = len(selected)
        for idx, item in enumerate(selected, 1):
            log(f"--- cleaning: {item.path}")
            remove_leftover(item, emit=log, dry_run=self.dry_run)
            self.progress.setValue(int(idx / n * 100))
        self.clean_btn.setEnabled(True)
        QMessageBox.information(self, "Linclear",
                                "Cleanup finished — see log for details.")
        self.accept()