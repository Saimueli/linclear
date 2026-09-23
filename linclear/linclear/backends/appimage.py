"""Find AppImages anywhere on the system.

Unlike the Manual backend (which only looks at fixed install dirs), this
scans the user's home and common locations, and optionally runs a bounded
`find` on the whole filesystem so nothing is missed.
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo, CAT_APP

HOME = Path.home()

# Directories we always scan (fast, no `find` needed)
QUICK_DIRS = [
    HOME / "Applications",
    HOME / "AppImages",
    HOME / "bin",
    HOME / ".local/bin",
    HOME / "Downloads",
    HOME / "Desktop",
    Path("/opt"),
    Path("/usr/local/bin"),
]

# Where we look for the `find` sweep. Root "/" catches everything but is slow;
# we cap depth and time.
SWEEP_ROOTS = [HOME, Path("/opt"), Path("/usr/local"), Path("/usr/share")]


def _extract_appimage_name(path: Path) -> str:
    """'Firefox-128.0-x86_64.AppImage' -> 'Firefox'."""
    stem = path.stem  # strips .AppImage
    # Strip architecture suffix
    for suffix in ("-x86_64", "-x86_64.AppImage", "-aarch64", "-arm64", ".x86_64"):
        if stem.lower().endswith(suffix.lower()):
            stem = stem[: -len(suffix)]
    # Strip version at end (e.g. "-128.0", "-2.10.36")
    parts = stem.rsplit("-", 1)
    if len(parts) == 2 and parts[1] and parts[1][0].isdigit():
        stem = parts[0]
    return stem or path.name


class AppImageBackend(Backend):
    source_name = "AppImage"
    command_name = "find"  # always available

    def is_available(self) -> bool:
        return True

    def list_apps(self) -> List[AppInfo]:
        """Quick scan of the standard directories (used on every refresh)."""
        apps: List[AppInfo] = []
        seen: set[str] = set()

        for d in QUICK_DIRS:
            if not d.is_dir():
                continue
            try:
                for f in d.iterdir():
                    if not f.is_file():
                        continue
                    if not os.access(f, os.X_OK):
                        continue
                    name = f.name
                    if not (name.endswith(".AppImage")
                            or name.endswith(".appimage")
                            or name.endswith(".AppImage.zsync")):
                        continue
                    if name.endswith(".zsync"):
                        continue
                    real = str(f.resolve())
                    if real in seen:
                        continue
                    seen.add(real)
                    apps.append(self._make_app(f))
            except PermissionError:
                continue

        return apps

    @staticmethod
    def _make_app(path: Path) -> AppInfo:
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        return AppInfo(
            name=_extract_appimage_name(path),
            package_id=path.name,
            source="AppImage",
            category=CAT_APP,
            size_bytes=size,
            install_path=str(path),
            description="Portable AppImage executable",
            extra={"paths": [str(path)]},
        )

    # ---- deep scan (called from the AppImage Finder dialog, in a thread) --
    def deep_scan(self, emit=None) -> List[AppInfo]:
        """Run a bounded `find` across the user's home and common dirs."""
        apps: List[AppInfo] = []
        seen: set[str] = set()

        # First, the quick scan
        for a in self.list_apps():
            seen.add(a.install_path)
            apps.append(a)

        if emit:
            emit(f"[appimage] deep scan across {len(SWEEP_ROOTS)} roots…")

        for root in SWEEP_ROOTS:
            if not root.is_dir():
                continue
            try:
                r = subprocess.run(
                    ["find", str(root), "-maxdepth", "6",
                     "-type", "f", "(", "-iname", "*.AppImage",
                     "-o", "-iname", "*.appimage", ")",
                     "-perm", "-u+x", "2>/dev/null"],
                    capture_output=True, text=True, timeout=25, check=False,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
            for line in r.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                p = Path(line)
                real = str(p.resolve())
                if real in seen:
                    continue
                seen.add(real)
                apps.append(self._make_app(p))
            if emit:
                emit(f"[appimage] {root}: {len(apps)} total so far")

        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        paths = [p for p in (app.extra.get("paths") or [app.install_path])
                 if p and os.path.exists(p)]
        if not paths:
            return []
        needs_root = any(not str(p).startswith(str(HOME)) for p in paths)
        return [(["rm", "-rf", "--", *paths], needs_root)]