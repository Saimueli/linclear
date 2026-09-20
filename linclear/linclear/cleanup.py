"""Scan for and remove files/packages left behind by an uninstalled app."""
import os
from pathlib import Path
from typing import Callable, List, Optional
from .models import AppInfo, LeftoverItem

HOME = Path.home()

USER_SEARCH_DIRS = [
    HOME / ".config", HOME / ".local/share", HOME / ".cache", HOME / ".local/bin",
]
SYSTEM_SEARCH_DIRS = [
    Path("/etc"), Path("/var/lib"), Path("/var/cache"),
    Path("/opt"), Path("/usr/local/share"), Path("/usr/local/lib"),
    Path("/usr/local/bin"),
]


def _safe_size(path: Path) -> int:
    try:
        if path.is_file() or path.is_symlink():
            return path.lstat().st_size
        total = 0
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    total += (Path(root) / f).lstat().st_size
                except OSError:
                    pass
        return total
    except OSError:
        return 0


def _candidate_names(app: AppInfo) -> set:
    out = set()
    for n in {app.name, app.package_id, app.package_id.split(".")[-1]}:
        if not n:
            continue
        n = n.strip().lower()
        if len(n) < 3:
            continue
        out.add(n)
        out.add(n.replace("-", ""))
        out.add(n.replace("_", ""))
        out.add(n.replace("-", "_"))
        out.add(n.split(".")[0])
    return {x for x in out if len(x) >= 3}


def _matches(name: str, candidates: set) -> bool:
    n = name.lower()
    for c in candidates:
        if n == c or n.startswith(c + "-") or n.startswith(c + "."):
            return True
    return False


def scan_leftovers(app: AppInfo,
                   emit: Optional[Callable[[str], None]] = None) -> List[LeftoverItem]:
    items: List[LeftoverItem] = []
    candidates = _candidate_names(app)

    def log(m):
        if emit:
            emit(m)

    log(f"[leftovers] scanning for '{app.name}' "
        f"(candidates: {sorted(candidates)})")

    for d in USER_SEARCH_DIRS:
        if not d.is_dir():
            continue
        try:
            for child in d.iterdir():
                if _matches(child.name, candidates):
                    items.append(LeftoverItem(
                        path=str(child),
                        kind="dir" if child.is_dir() else "file",
                        size_bytes=_safe_size(child),
                        reason=f"Matches '{app.name}' in {d}",
                        category="User files",
                    ))
        except PermissionError:
            pass

    for d in SYSTEM_SEARCH_DIRS:
        if not d.is_dir():
            continue
        try:
            for child in d.iterdir():
                if not _matches(child.name, candidates):
                    continue
                items.append(LeftoverItem(
                    path=str(child),
                    kind="dir" if child.is_dir() else "file",
                    size_bytes=_safe_size(child),
                    reason=f"Matches '{app.name}' in {d}",
                    category="System files",
                ))
        except PermissionError:
            pass

    # Package-manager cleanup commands
    if app.source == "RPM":
        items.append(LeftoverItem(
            path="dnf autoremove", kind="command",
            reason="Remove orphaned RPM dependencies",
            category="Package cleanup"))
    if app.source == "DEB":
        items.append(LeftoverItem(
            path="apt-get autoremove", kind="command",
            reason="Remove orphaned DEB dependencies",
            category="Package cleanup"))
    if app.source == "Flatpak":
        items.append(LeftoverItem(
            path="flatpak uninstall --unused", kind="command",
            reason="Remove unused Flatpak runtimes",
            category="Package cleanup"))

    # Broken symlinks
    for d in (HOME / ".local/bin", Path("/usr/local/bin")):
        if not d.is_dir():
            continue
        try:
            for child in d.iterdir():
                if child.is_symlink() and not child.exists():
                    target = os.readlink(child)
                    if any(c in target.lower() for c in candidates):
                        items.append(LeftoverItem(
                            path=str(child), kind="symlink",
                            reason=f"Broken symlink → {target}",
                            category="Broken symlinks"))
        except PermissionError:
            pass

    return items


def remove_leftover(item: LeftoverItem, emit: Callable[[str], None],
                    dry_run: bool = False) -> int:
    from .privileged import run_command
    if item.kind == "command":
        if item.path == "dnf autoremove":
            return run_command(["dnf", "autoremove", "-y"],
                               emit=emit, privileged=True, dry_run=dry_run)
        if item.path == "apt-get autoremove":
            return run_command(["apt-get", "autoremove", "--purge", "-y"],
                               emit=emit, privileged=True, dry_run=dry_run)
        if item.path == "flatpak uninstall --unused":
            return run_command(["flatpak", "uninstall", "--unused", "-y"],
                               emit=emit, dry_run=dry_run)
        return 0
    needs_root = not item.path.startswith(str(HOME))
    return run_command(["rm", "-rf", "--", item.path],
                       emit=emit, privileged=needs_root, dry_run=dry_run)