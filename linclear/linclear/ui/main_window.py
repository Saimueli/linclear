from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QLineEdit,
    QComboBox, QListWidget, QListWidgetItem, QLabel, QPushButton,
    QPlainTextEdit, QProgressBar, QToolBar, QMessageBox, QInputDialog,
    QFormLayout, QGroupBox, QApplication, QStyledItemDelegate, QStyle,
)
from PyQt6.QtCore import Qt, QSettings, QThread, pyqtSignal, QSize, QRect
from PyQt6.QtGui import QAction, QFont, QColor

from .. import __version__
from ..models import AppInfo
from ..worker import ListAppsWorker, CommandWorker
from ..backends import get_backends
from .. import safety
from ..cleanup import scan_leftovers
from .theme import apply_theme
from .leftovers_dialog import LeftoversDialog
from .settings_dialog import SettingsDialog


# ---------------------------------------------------------------- delegate --
class AppRowDelegate(QStyledItemDelegate):
    """Render each row in fixed structured columns:
    [ Name (flex) ] [ Badge (70px) ] [ Version (150px) ] [ Size (75px) ]
    """

    SOURCE_COLORS = {
        "RPM":     "#c9624a",
        "DEB":     "#a83a56",
        "Snap":    "#b5651d",
        "Flatpak": "#4a7ec9",
        "Manual":  "#6a8c6a",
    }

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 36)

    def paint(self, painter, option, index):
        app = index.data(Qt.ItemDataRole.UserRole)
        if app is None:
            super().paint(painter, option, index)
            return

        painter.save()

        # Selection state styling
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            name_color = option.palette.highlightedText().color()
            meta_color = name_color
        else:
            name_color = option.palette.text().color()
            meta_color = QColor(name_color)
            meta_color.setAlpha(160)

        rect = option.rect.adjusted(10, 0, -10, 0)
        cy = rect.center().y()

        # Defined column layout bounds from right to left
        SIZE_WIDTH = 75
        VERSION_WIDTH = 150
        BADGE_WIDTH = 68
        SPACING = 12

        size_x = rect.right() - SIZE_WIDTH
        ver_x = size_x - SPACING - VERSION_WIDTH
        badge_x = ver_x - SPACING - BADGE_WIDTH
        name_max_w = badge_x - SPACING - rect.left()

        # Font setup for metadata
        meta_font = QFont(option.font)
        meta_font.setPointSizeF(option.font.pointSizeF() - 0.5)
        painter.setFont(meta_font)

        # 1. Size column (far right)
        if app.size_bytes:
            size_rect = QRect(size_x, rect.top(), SIZE_WIDTH, rect.height())
            painter.setPen(meta_color)
            painter.drawText(
                size_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                app.size_human
            )

        # 2. Version column (fixed width with elision)
        if app.version:
            ver_rect = QRect(ver_x, rect.top(), VERSION_WIDTH, rect.height())
            painter.setPen(meta_color)
            elided_ver = painter.fontMetrics().elidedText(
                app.version, Qt.TextElideMode.ElideRight, VERSION_WIDTH
            )
            painter.drawText(
                ver_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                elided_ver
            )

        # 3. Source Badge column (fixed width badge)
        badge_rect = QRect(badge_x, cy - 10, BADGE_WIDTH, 20)
        badge_color = QColor(self.SOURCE_COLORS.get(app.source, "#888888"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(badge_color)
        painter.drawRoundedRect(badge_rect, 4, 4)

        badge_font = QFont(option.font)
        badge_font.setPointSizeF(option.font.pointSizeF() - 1.5)
        badge_font.setBold(True)
        painter.setFont(badge_font)
        painter.setPen(QColor("white"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, app.source)

        # 4. App Name column (fills remaining left space, bold, elided)
        if name_max_w > 30:
            name_rect = QRect(rect.left(), rect.top(), name_max_w, rect.height())
            name_font = QFont(option.font)
            name_font.setBold(True)
            painter.setFont(name_font)
            painter.setPen(name_color)
            elided_name = painter.fontMetrics().elidedText(
                app.name, Qt.TextElideMode.ElideRight, name_rect.width()
            )
            painter.drawText(
                name_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                elided_name
            )

        painter.restore()


# ----------------------------------------------------------- leftover worker --
class LeftoverWorker(QThread):
    output = pyqtSignal(str)
    done   = pyqtSignal(list)

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):
        try:
            items = scan_leftovers(self.app, emit=self.output.emit)
        except Exception as e:
            self.output.emit(f"[error] {e}")
            items = []
        self.done.emit(items)


# --------------------------------------------------------------- main window --
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linclear — Linux App Uninstaller & Cleaner")
        self.resize(1240, 780)

        self.settings = QSettings("Linclear", "Linclear")
        self.backends = get_backends()
        self.apps: list[AppInfo] = []
        self.current: AppInfo | None = None
        self._worker = None
        self._lw = None

        self._build_ui()
        self._apply_settings()
        self.log(f"Linclear {__version__} starting…")
        self.refresh()

    # ------------------------------------------------------------- UI setup --
    def _build_ui(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        self.act_refresh = QAction("Refresh", self)
        self.act_refresh.triggered.connect(self.refresh)
        tb.addAction(self.act_refresh)
        tb.addSeparator()

        self.act_uninstall = QAction("Uninstall", self)
        self.act_uninstall.triggered.connect(self.uninstall_selected)
        tb.addAction(self.act_uninstall)

        self.act_leftovers = QAction("Scan Leftovers", self)
        self.act_leftovers.triggered.connect(self.scan_leftovers_for_selected)
        tb.addAction(self.act_leftovers)

        self.act_settings = QAction("Settings", self)
        self.act_settings.triggered.connect(self.open_settings)
        tb.addAction(self.act_settings)
        tb.addSeparator()

        self.act_about = QAction("About", self)
        self.act_about.triggered.connect(self.about)
        tb.addAction(self.act_about)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter, 1)

        # -------------------- left pane --------------------
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(8, 8, 8, 8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search apps…")
        self.search.textChanged.connect(self._refilter)
        ll.addWidget(self.search)

        self.source_filter = QComboBox()
        self.source_filter.addItem("All sources")
        for b in self.backends:
            self.source_filter.addItem(b.source_name)
        self.source_filter.currentIndexChanged.connect(self._refilter)
        ll.addWidget(self.source_filter)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Name (A → Z)",
            "Name (Z → A)",
            "Size (largest → smallest)",
            "Size (smallest → largest)",
            "Source, then name",
        ])
        self.sort_combo.currentIndexChanged.connect(self._refilter)
        ll.addWidget(self.sort_combo)

        self.list = QListWidget()
        self.list.setItemDelegate(AppRowDelegate(self.list))
        self.list.setUniformItemSizes(True)
        self.list.setSpacing(0)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.currentItemChanged.connect(self._on_select)
        ll.addWidget(self.list, 1)

        self.count_label = QLabel("0 apps")
        self.count_label.setObjectName("subtitle")
        ll.addWidget(self.count_label)
        splitter.addWidget(left)

        # -------------------- right pane --------------------
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 8, 8, 8)

        self.title_label = QLabel("Select an application")
        self.title_label.setObjectName("title")
        self.title_label.setWordWrap(True)
        rl.addWidget(self.title_label)

        box = QGroupBox("Details")
        form = QFormLayout(box)
        self.d_name    = QLabel("—")
        self.d_version = QLabel("—")
        self.d_source  = QLabel("—")
        self.d_size    = QLabel("—")
        self.d_path    = QLabel("—")
        self.d_path.setWordWrap(True)
        self.d_desc    = QLabel("—")
        self.d_desc.setWordWrap(True)
        form.addRow("Name:", self.d_name)
        form.addRow("Version:", self.d_version)
        form.addRow("Source:", self.d_source)
        form.addRow("Size:", self.d_size)
        form.addRow("Install path:", self.d_path)
        form.addRow("Description:", self.d_desc)
        rl.addWidget(box)

        row = QHBoxLayout()
        self.btn_uninstall = QPushButton("Uninstall")
        self.btn_uninstall.setObjectName("danger")
        self.btn_uninstall.clicked.connect(self.uninstall_selected)
        self.btn_leftovers = QPushButton("Scan Leftovers")
        self.btn_leftovers.clicked.connect(self.scan_leftovers_for_selected)
        row.addWidget(self.btn_uninstall)
        row.addWidget(self.btn_leftovers)
        row.addStretch(1)
        rl.addLayout(row)
        rl.addStretch(1)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        # -------------------- log --------------------
        log_box = QGroupBox("Log")
        ll2 = QVBoxLayout(log_box)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        ll2.addWidget(self.log_view)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        ll2.addWidget(self.progress)
        root.addWidget(log_box, 0)

    # ------------------------------------------------------------- helpers --
    def log(self, msg: str):
        self.log_view.appendPlainText(msg)

    def _busy(self, on: bool):
        self.progress.setVisible(on)
        for a in (self.act_refresh, self.act_uninstall, self.act_leftovers):
            a.setEnabled(not on)
        self.btn_uninstall.setEnabled(not on)
        self.btn_leftovers.setEnabled(not on)

    def _apply_settings(self):
        theme = self.settings.value("theme", "Dark")
        apply_theme(QApplication.instance(), dark=(theme != "Light"))

    # ------------------------------------------------------------- listing --
    def refresh(self):
        self.log("[refresh] enumerating installed apps…")
        self._busy(True)
        self._worker = ListAppsWorker(self.backends)
        self._worker.output.connect(self.log)
        self._worker.done.connect(self._on_apps)
        self._worker.start()

    def _on_apps(self, apps):
        self._busy(False)
        self.apps = list(apps)
        self._refilter()
        self.log(f"[refresh] {len(self.apps)} apps total")

    def _refilter(self):
        text = self.search.text().lower().strip()
        src = self.source_filter.currentText()
        show_manual = self.settings.value("show_manual", True, type=bool)

        visible = []
        for a in self.apps:
            if src != "All sources" and a.source != src:
                continue
            if not show_manual and a.source == "Manual":
                continue
            if text and text not in a.name.lower() and text not in a.package_id.lower():
                continue
            visible.append(a)

        visible.sort(key=self._sort_key())

        self.list.clear()
        for a in visible:
            item = QListWidgetItem(a.name)
            item.setData(Qt.ItemDataRole.UserRole, a)
            item.setSizeHint(QSize(0, 36))
            self.list.addItem(item)

        self.count_label.setText(f"{len(visible)} of {len(self.apps)} apps")

    def _sort_key(self):
        mode = self.sort_combo.currentText()
        if mode == "Name (A → Z)":
            return lambda a: (0, a.name.lower())
        if mode == "Name (Z → A)":
            return lambda a: (0, tuple(-ord(c) for c in a.name.lower()))
        if mode == "Size (largest → smallest)":
            return lambda a: (0, -(a.size_bytes or 0), a.name.lower())
        if mode == "Size (smallest → largest)":
            return lambda a: (0, (a.size_bytes or 0), a.name.lower())
        if mode == "Source, then name":
            return lambda a: (0, a.source.lower(), a.name.lower())
        return lambda a: (0, a.name.lower())

    def _on_select(self, cur, _prev):
        if cur is None:
            self.current = None
            return
        a: AppInfo = cur.data(Qt.ItemDataRole.UserRole)
        self.current = a
        self.title_label.setText(a.name)
        self.d_name.setText(a.name)
        self.d_version.setText(a.version or "—")
        self.d_source.setText(a.source)
        self.d_size.setText(a.size_human)
        self.d_path.setText(a.install_path or "—")
        self.d_desc.setText(a.description or "—")

    # ----------------------------------------------------------- uninstall --
    def uninstall_selected(self):
        a = self.current
        if not a:
            QMessageBox.information(self, "Linclear", "Select an application first.")
            return
        backend = next((b for b in self.backends if b.source_name == a.source), None)
        if not backend:
            QMessageBox.warning(self, "Linclear", f"No backend for '{a.source}'")
            return

        plan = backend.plan_uninstall(a)
        if not plan:
            QMessageBox.warning(self, "Linclear", "Nothing to uninstall (empty plan).")
            return

        if safety.is_critical(a.package_id):
            QMessageBox.critical(
                self, "Protected package",
                f"'{a.package_id}' is on Linclear's protected list and will not be removed.\n"
                "Removing it could break your system.")
            return

        cmd_text = "\n".join(
            ("sudo " if root else "") + " ".join(cmd) for cmd, root in plan)

        needs_typed = (a.source in ("RPM", "DEB") and
                       self.settings.value("require_confirm", True, type=bool))

        if needs_typed:
            typed, ok = QInputDialog.getText(
                self, "Confirm uninstall",
                f"This will uninstall the SYSTEM package '{a.name}'.\n\n"
                f"Commands:\n{cmd_text}\n\n"
                f"Type '{a.package_id}' to confirm:")
            if not ok or typed.strip() != a.package_id:
                self.log("[abort] confirmation failed")
                return
        else:
            if QMessageBox.question(
                self, "Confirm uninstall",
                f"Uninstall '{a.name}' ({a.source})?\n\nCommands:\n{cmd_text}"
            ) != QMessageBox.StandardButton.Yes:
                return

        dry = self.settings.value("dry_run", False, type=bool)
        if dry:
            self.log("[dry-run] no changes will be made")

        self._busy(True)
        self.log(f"=== Uninstalling {a.name} ({a.source}) ===")
        self._worker = CommandWorker(
            lambda emit: backend.uninstall(a, emit=emit, dry_run=dry))
        self._worker.output.connect(self.log)
        self._worker.done.connect(self._on_uninstall_done)
        self._worker.start()

    def _on_uninstall_done(self, rc):
        self._busy(False)
        self.log(f"=== Uninstall finished (rc={rc}) ===")
        target = self.current
        self.refresh()
        if target and QMessageBox.question(
            self, "Scan for leftovers?",
            "Uninstall finished. Scan for leftover files ('crumbs')?"
        ) == QMessageBox.StandardButton.Yes:
            self.current = target
            self.scan_leftovers_for_selected()

    # ----------------------------------------------------------- leftovers --
    def scan_leftovers_for_selected(self):
        a = self.current
        if not a:
            QMessageBox.information(self, "Linclear", "Select an application first.")
            return
        self._busy(True)
        self.log(f"=== Scanning leftovers for {a.name} ===")
        self._lw = LeftoverWorker(a)
        self._lw.output.connect(self.log)
        self._lw.done.connect(self._show_leftovers)
        self._lw.start()

    def _show_leftovers(self, items):
        self._busy(False)
        if not items:
            QMessageBox.information(self, "Linclear",
                                    "No leftover items found. Nice and clean!")
            return
        self.log(f"[leftovers] {len(items)} item(s) found")
        dlg = LeftoversDialog(
            self.current, items, parent=self,
            dry_run=self.settings.value("dry_run", False, type=bool))
        dlg.exec()

    # ------------------------------------------------------------ settings --
    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            dlg.save()
            self._apply_settings()
            self._refilter()
            self.log("[settings] saved")

    def about(self):
        QMessageBox.about(
            self, "About Linclear",
            f"<h3>Linclear {__version__}</h3>"
            "<p>A universal Linux application uninstaller and system cleaner.</p>"
            "<p>Supports RPM, DEB, Snap, Flatpak, and manually-installed apps.</p>"
            "<p><b>Created by Saimueli</b><br>"
            "<a href='https://github.com/Saimueli'>github.com/Saimueli</a></p>"
            "<p>MIT Licensed.</p>")
