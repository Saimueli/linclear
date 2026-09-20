from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QCheckBox,
                             QDialogButtonBox, QComboBox, QLabel)
from PyQt6.QtCore import QSettings


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Linclear — Settings")
        self.setMinimumWidth(380)
        self.settings = QSettings("Linclear", "Linclear")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.dry_run = QCheckBox("Dry-run mode (log actions but don't remove anything)")
        self.dry_run.setChecked(self.settings.value("dry_run", False, type=bool))
        form.addRow(self.dry_run)

        self.require_confirm = QCheckBox(
            "Require typed confirmation for system packages (RPM/DEB)")
        self.require_confirm.setChecked(
            self.settings.value("require_confirm", True, type=bool))
        form.addRow(self.require_confirm)

        self.show_manual = QCheckBox(
            "Include Manual / Script-installed apps in the list")
        self.show_manual.setChecked(
            self.settings.value("show_manual", True, type=bool))
        form.addRow(self.show_manual)

        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light"])
        self.theme.setCurrentText(self.settings.value("theme", "Dark"))
        form.addRow(QLabel("Theme:"), self.theme)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        self.settings.setValue("dry_run", self.dry_run.isChecked())
        self.settings.setValue("require_confirm", self.require_confirm.isChecked())
        self.settings.setValue("show_manual", self.show_manual.isChecked())
        self.settings.setValue("theme", self.theme.currentText())