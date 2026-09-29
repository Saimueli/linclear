"""Linclear main window."""

import os
from html import escape

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QAction, QColor, QPainter
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QSplitter, QStyle,
    QStyledItemDelegate, QTextBrowser, QToolBar, QVBoxLayout, QWidget,
)

from .. import backends, privileged, safety, version
from ..models import AppInfo
from ..workers import CommandWorker, FunctionWorker
from .appimage_dialog import AppImageDialog
from .leftovers_dialog import LeftoversDialog
from .theme import DEFAULT_SOURCE_COLOR, SOURCE_COLORS, get_qss


# --------------------------------------------------------------- delegate

class AppDelegate(QStyledItemDelegate):
    """Paints one application row: name | version | size | badge."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.light = False

    def sizeHint(self, option, index) -> QSize:  # noqa: N802
        return QSize(240, 34)

    def paint(self, painter: QPainter, option, index):
        app = index.data(Qt.ItemDataRole.UserRole)
        rect = option.rect

        painter.save()

        if self.light:
            selected_bg = QColor("#d8e3fb")
            hover_bg = QColor("#eef1f6")
            name_color = QColor("#1e1f22")
            meta_color = QColor("#6b7075")
        else:
            selected_bg = QColor("#3a3f4b")
            hover_bg = QColor("#2f3238")
            name_color = QColor("#e6e6e6")
            meta_color = QColor("#9aa0a6")

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, selected_bg)
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(rect, hover_bg)

        if app is None:
            painter.restore()
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        metrics = painter.fontMetrics()

        # --- badge -----------------------------------------------------
        badge_text = (app.source or "").upper() or "?"
        badge_width = metrics.horizontalAdvance(badge_text) + 18
        badge_height = 18
        badge_x = rect.right() - badge_width - 10
        badge_y = rect.top() + (rect.height() - badge_height) // 2

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(SOURCE_COLORS.get(app.source, DEFAULT_SOURCE_COLOR)))
        painter.drawRoundedRect(badge_x, badge_y, badge_width, badge_height, 4, 4)
        painter.setPen(QColor("#ffffff"))
        painter.drawText(
            QRect(badge_x, badge_y, badge_width, badge_height),
            Qt.AlignmentFlag.AlignCenter, badge_text,
        )

        # --- meta (version + size) ------------------------------------
        meta_width = min(220, max(90, int(rect.width() * 0.30)))
        meta_rect = QRect(badge_x - meta_width - 10, rect.top(), meta_width, rect.height())
        meta_text = f"{app.version}   {app.size_str}".strip()
        painter.setPen(meta_color)
        painter.drawText(
            meta_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            metrics.elidedText(meta_text, Qt.TextElideMode.ElideRight, meta_rect.width()),
        )

        # --- name ------------------------------------------------------
        name_rect = QRect(
            rect.left() + 12, rect.top(),
            max(40, meta_rect.left() - rect.left() - 24), rect.height(),
        )
        painter.setPen(name_color)
        painter.drawText(
            name_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            metrics.elidedText(app.name, Qt.TextElideMode.ElideRight, name_rect.width()),
        )

        painter.restore()


# --------------------------------------------------------------- window

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{version.APP_NAME} {version.APP_VERSION}")
        self.resize(1200, 760)

        self._all_apps: list = []
        self._workers: list = []
        self._pending = 0
        self._queue: list = []
        self._uninstalled: list = []
        self._cmd_worker = None
        self._retried = False
        self._light = False
        self._appimage_changed = False

        self._build_ui()
        self.apply_theme()
        self.refresh()

    # ---------------------------------------------------------------- UI

    def _build_ui(self):
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(toolbar)

        self.act_refresh = QAction("Refresh", self)
        self.act_refresh.setShortcut("F5")
        self.act_refresh.triggered.connect(self.refresh)
        toolbar.addAction(self.act_refresh)

        self.act_uninstall = QAction("Uninstall", self)
        self.act_uninstall.setShortcut("Ctrl+Delete")
        self.act_uninstall.triggered.connect(self._on_uninstall)
        toolbar.addAction(self.act_uninstall)

        toolbar.addSeparator()

        self.act_leftovers = QAction("Scan Leftovers", self)
        self.act_leftovers.triggered.connect(self._on_leftovers)
        toolbar.addAction(self.act_leftovers)

        self.act_appimages = QAction("Find AppImages", self)
        self.act_appimages.triggered.connect(self._on_appimages)
        toolbar.addAction(self.act_appimages)

        toolbar.addSeparator()

        self.act_settings = QAction("Settings", self)
        self.act_settings.triggered.connect(self._on_settings)
        toolbar.addAction(self.act_settings)

        self.act_about = QAction("About", self)
        self.act_about.triggered.connect(self._on_about)
        toolbar.addAction(self.act_about)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # -------- filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(6)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search applications…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._populate)
        filter_bar.addWidget(self.search, 1)

        self.source_filter = QComboBox()
        self.source_filter.addItem("All sources")
        for name, _ in backends.BACKENDS:
            self.source_filter.addItem(name)
        self.source_filter.currentIndexChanged.connect(self._populate)
        filter_bar.addWidget(self.source_filter)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name", "Size", "Source"])
        self.sort_combo.currentIndexChanged.connect(self._populate)
        filter_bar.addWidget(self.sort_combo)

        root.addLayout(filter_bar)

        # -------- splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setMouseTracking(True)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setItemDelegate(AppDelegate(self.list_widget))
        self.list_widget.currentItemChanged.connect(self._show_details)
        splitter.addWidget(self.list_widget)

        self.details = QTextBrowser()
        splitter.addWidget(self.details)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([720, 440])
        root.addWidget(splitter, 1)

        # -------- log + progress
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(3000)
        self.log_view.setFixedHeight(140)
        root.addWidget(self.log_view)

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.status = self.statusBar()
        self.status.showMessage("Ready")

    # ---------------------------------------------------------------- theme

    def apply_theme(self):
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(get_qss(self._light))
        delegate = self.list_widget.itemDelegate()
        if isinstance(delegate, AppDelegate):
            delegate.light = self._light
        self.list_widget.viewport().update()

    # ---------------------------------------------------------------- log

    def log(self, text):
        if text is None:
            return
        self.log_view.appendPlainText(str(text))

    # ---------------------------------------------------------------- scan

    def refresh(self):
        self.log("Scanning installed applications…")
        self.status.showMessage("Scanning…")
        self.progress.setRange(0, 0)

        self._all_apps = []
        self._workers = []
        self._pending = len(backends.BACKENDS)

        for name, fn in backends.BACKENDS:
            worker = FunctionWorker(fn)
            worker.done.connect(lambda apps, n=name: self._on_backend_done(n, apps))
            worker.failed.connect(lambda msg, n=name: self._on_backend_failed(n, msg))
            worker.finished.connect(worker.deleteLater)
            self._workers.append(worker)
            worker.start()

    def _on_backend_done(self, name, apps):
        apps = list(apps or [])
        self._all_apps.extend(apps)
        if apps:
            self.log(f"  {name:<9} {len(apps)} item(s)")
        self._finish_backend()

    def _on_backend_failed(self, name, message):
        self.log(f"  {name:<9} failed: {message}")
        self._finish_backend()

    def _finish_backend(self):
        self._pending -= 1
        if self._pending > 0:
            return
        self._pending = 0
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self._populate()
        self.status.showMessage(f"{len(self._all_apps)} applications found")
        self.log(f"Scan complete — {len(self._all_apps)} item(s).")

    # ---------------------------------------------------------------- list

    def _populate(self):
        query = self.search.text().strip().lower()
        source = self.source_filter.currentText()
        sort_key = self.sort_combo.currentText()

        apps = self._all_apps

        if source and source != "All sources":
            apps = [a for a in apps if a.source == source]

        if query:
            def matches(app: AppInfo) -> bool:
                return (
                    query in app.name.lower()
                    or query in app.package.lower()
                    or query in app.description.lower()
                    or query in app.category.lower()
                )
            apps = [a for a in apps if matches(a)]

        apps = list(apps)
        if sort_key == "Name":
            apps.sort(key=lambda a: a.name.lower())
        elif sort_key == "Size":
            apps.sort(key=lambda a: a.size, reverse=True)
        else:
            apps.sort(key=lambda a: (a.source, a.name.lower()))

        self.list_widget.setUpdatesEnabled(False)
        self.list_widget.clear()
        for app in apps:
            item = QListWidgetItem(app.name)
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.list_widget.addItem(item)
        self.list_widget.setUpdatesEnabled(True)

        self.status.showMessage(f"{len(apps)} / {len(self._all_apps)} shown")

    # ---------------------------------------------------------------- details

    def _show_details(self, current, _previous=None):
        if current is None:
            self.details.setHtml("")
            return
        app = current.data(Qt.ItemDataRole.UserRole)
        if app is None:
            self.details.setHtml("")
            return

        color = SOURCE_COLORS.get(app.source, DEFAULT_SOURCE_COLOR)
        cmd = privileged.display(app.uninstall_cmd) if app.uninstall_cmd else "—"
        protected = safety.is_critical(app.package or app.name)

        parts = []
        parts.append('<div style="font-family: sans-serif; font-size: 10pt;">')
        parts.append(f'<h2 style="margin:0 0 6px 0;">{escape(app.name)}</h2>')
        parts.append(
            f'<span style="background:{color}; color:#ffffff; padding:2px 8px; '
            f'border-radius:4px; font-size:9pt;">{escape(app.source)}</span>'
        )
        if protected:
            parts.append(
                ' <span style="background:#8a2b2b; color:#ffffff; padding:2px 8px; '
                'border-radius:4px; font-size:9pt;">PROTECTED</span>'
            )
        parts.append(
            f'<p style="color:#9aa0a6; margin:12px 0;">'
            f'{escape(app.description or "No description available.")}</p>'
        )
        parts.append('<table cellpadding="4" cellspacing="0">')
        rows = [
            ("Package", app.package or "—"),
            ("Version", app.version or "—"),
            ("Size", app.size_str),
            ("Category", app.category or "—"),
            ("Path", app.path or "—"),
            ("Root required", "yes" if app.needs_root else "no"),
        ]
        for label, value in rows:
            parts.append(
                f'<tr><td style="color:#9aa0a6; padding-right:14px;">{escape(label)}</td>'
                f'<td>{escape(str(value))}</td></tr>'
            )
        parts.append("</table>")
        parts.append(
            '<p style="color:#9aa0a6; margin-top:14px;">Uninstall command</p>'
            f'<pre style="background:#111214; padding:8px; border-radius:6px; '
            f'white-space:pre-wrap;">{escape(cmd)}</pre>'
        )
        parts.append("</div>")

        self.details.setHtml("".join(parts))

    # ---------------------------------------------------------------- uninstall

    def _selected_apps(self):
        result = []
        for item in self.list_widget.selectedItems():
            app = item.data(Qt.ItemDataRole.UserRole)
            if app is not None:
                result.append(app)
        return result

    def _effective_command(self, app: AppInfo):
        return privileged.effective_command(app.uninstall_cmd, app.needs_root)

    def _on_uninstall(self):
        apps = self._selected_apps()
        if not apps:
            QMessageBox.information(self, "Uninstall",
                                    "Select one or more applications first.")
            return

        blocked = [a for a in apps if safety.is_critical(a.package or a.name)]
        if blocked:
            names = "\n".join(f"  • {a.name}" for a in blocked)
            QMessageBox.warning(
                self, "Protected packages",
                "These packages are protected and will be skipped:\n\n" + names,
            )
            apps = [a for a in apps if a not in blocked]

        if not apps:
            return

        lines = []
        for app in apps:
            cmd = self._effective_command(app)
            cmd_text = privileged.display(cmd) if cmd else "(no command available)"
            lines.append(f"• {app.name}  [{app.source}]\n    {cmd_text}")

        message = ("The following commands will be executed:\n\n"
                   + "\n".join(lines) + "\n\nProceed?")
        answer = QMessageBox.question(
            self, "Confirm uninstall", message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self._queue = list(apps)
        self._uninstalled = list(apps)
        self.progress.setRange(0, max(1, len(apps)))
        self.progress.setValue(0)
        self._process_next()

    def _process_next(self):
        if not self._queue:
            self.log("All commands finished.")
            self._ask_leftovers()
            return

        app = self._queue.pop(0)
        cmd = self._effective_command(app)
        if not cmd:
            self.log(f"Skipping {app.name}: no usable uninstall command.")
            self._process_next()
            return

        self._retried = False
        self._launch(app, cmd)

    def _launch(self, app: AppInfo, cmd):
        self.log("$ " + privileged.display(cmd))
        worker = CommandWorker(cmd)
        worker.line.connect(self.log)
        worker.finished_rc.connect(lambda rc: self._on_command_finished(rc, app))
        worker.finished.connect(worker.deleteLater)
        self._cmd_worker = worker
        worker.start()

    def _on_command_finished(self, rc: int, app: AppInfo):
        self.log(f"[{app.name}] exit code: {rc}")
        self.progress.setValue(min(self.progress.value() + 1, self.progress.maximum()))

        if rc in (126, 127) and app.needs_root and not self._retried:
            term = privileged.terminal_command(list(app.uninstall_cmd))
            if term is not None:
                self._retried = True
                self.log("Elevation failed — retrying in a terminal window…")
                self._launch(app, term)
                return

        self._process_next()

    def _ask_leftovers(self):
        apps = self._uninstalled
        self._uninstalled = []

        if apps:
            answer = QMessageBox.question(
                self, "Leftover files",
                "Scan for leftover files from the removed applications?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Yes:
                LeftoversDialog(apps, self).exec()

        self.refresh()

    # ---------------------------------------------------------------- toolbar

    def _on_leftovers(self):
        apps = self._selected_apps()
        if not apps:
            QMessageBox.information(self, "Leftovers",
                                    "Select an application in the list first.")
            return
        LeftoversDialog(apps, self).exec()

    def _on_appimages(self):
        dialog = AppImageDialog(self)
        dialog.exec()
        if dialog.changed:
            self.refresh()

    def _on_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Theme:"))
        combo = QComboBox()
        combo.addItems(["Dark", "Light"])
        combo.setCurrentText("Light" if self._light else "Dark")
        layout.addWidget(combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._light = combo.currentText() == "Light"
            self.apply_theme()

    def _on_about(self):
        QMessageBox.about(
            self,
            f"About {version.APP_NAME}",
            f"<h3>{version.APP_NAME} {version.APP_VERSION}</h3>"
            f"<p>{version.APP_TAGLINE}</p>"
            "<p>Supports DEB, RPM, Pacman, Snap, Flatpak, AppImage and "
            "manually installed .desktop applications.</p>"
            "<p style='color:#9aa0a6;'>Distributed exclusively as an AppImage.</p>",
        )