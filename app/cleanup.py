"""Leftover detection and removal."""

import os
import re
import shutil
import stat
from typing import Iterable, List, Union

from . import privileged
from .models import AppInfo, LeftoverItem

HOME = os.path.expanduser("~")

USER_DIRS = [
    os.path.join(HOME, ".config"),
    os.path.join(HOME, ".local", "share"),
    os.path.join(HOME, ".cache"),
    os.path.join(HOME, ".local", "bin"),
]

SYSTEM_DIRS = ["/etc", "/var/lib", "/opt"]

_NORM_RE = re.compile(r"[-_.\s]+")


def normalize(text: str) -> str:
    return _NORM_RE.sub("", (text or "")).lower()


def _candidate_keys(app: AppInfo) -> set:
    keys = set()
    raws = [app.package, app.name]
    if app.path:
        raws.append(os.path.basename(app.path))
    for raw in raws:
        if not raw:
            continue
        low = raw.lower()
        if low.endswith(".desktop"):
            raw = raw[: -len(".desktop")]
        elif low.endswith(".appimage"):
            raw = raw[: -len(".appimage")]
        norm = normalize(raw)
        if len(norm) >= 3:
            keys.add(norm)
    return keys


def _entry_size(path: str, max_files: int = 4000) -> int:
    try:
        st = os.lstat(path)
    except OSError:
        return 0

    if not stat.S_ISDIR(st.st_mode):
        return st.st_size

    total = 0
    count = 0
    for root, _dirs, files in os.walk(path):
        for filename in files:
            count += 1
            if count > max_files:
                return total
            try:
                total += os.lstat(os.path.join(root, filename)).st_size
            except OSError:
                pass
    return total


def find_leftovers(apps: Union[AppInfo, Iterable[AppInfo]]) -> List[LeftoverItem]:
    if isinstance(apps, AppInfo):
        apps = [apps]

    keys = set()
    for app in apps:
        keys |= _candidate_keys(app)
    if not keys:
        return []

    results: List[LeftoverItem] = []
    seen = set()

    for base in USER_DIRS + SYSTEM_DIRS:
        if not os.path.isdir(base):
            continue
        needs_root = base in SYSTEM_DIRS
        try:
            entries = os.listdir(base)
        except OSError:
            continue
        for entry in entries:
            path = os.path.join(base, entry)
            if path in seen:
                continue
            norm = normalize(entry)
            if len(norm) < 3:
                continue

            matched = False
            for key in keys:
                if norm == key or (len(key) >= 5 and norm.startswith(key)):
                    matched = True
                    break
            if not matched:
                continue

            seen.add(path)
            is_dir = os.path.isdir(path) and not os.path.islink(path)
            results.append(LeftoverItem(
                path=path,
                kind="dir" if is_dir else "file",
                size=_entry_size(path),
                needs_root=needs_root,
            ))

    results.sort(key=lambda item: (item.needs_root, item.path))
    return results


def find_broken_symlinks() -> List[LeftoverItem]:
    results: List[LeftoverItem] = []
    for base in (os.path.join(HOME, ".local", "bin"), "/usr/local/bin"):
        if not os.path.isdir(base):
            continue
        needs_root = base.startswith("/usr")
        try:
            entries = os.listdir(base)
        except OSError:
            continue
        for entry in entries:
            path = os.path.join(base, entry)
            if os.path.islink(path) and not os.path.exists(path):
                results.append(LeftoverItem(
                    path=path, kind="symlink", size=0, needs_root=needs_root,
                ))
    return results


def remove_items(items: Iterable[LeftoverItem]) -> List[str]:
    """Remove leftovers. Returns log lines (never raises)."""
    items = list(items)
    logs: List[str] = []

    user_paths = [i.path for i in items if not i.needs_root]
    root_paths = [i.path for i in items if i.needs_root]

    for path in user_paths:
        try:
            if os.path.islink(path) or os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            logs.append(f"removed  {path}")
        except OSError as exc:
            logs.append(f"FAILED   {path}: {exc}")

    if root_paths:
        cmd = ["rm", "-rf"] + root_paths
        full = privileged.effective_command(cmd, needs_root=True)
        if full is None:
            logs.append("ERROR: cannot elevate privileges to remove system leftovers.")
        else:
            logs.append("$ " + privileged.display(full))
            rc, out, err = privileged.run(full, timeout=600)
            if out.strip():
                logs.append(out.strip())
            if err.strip():
                logs.append(err.strip())
            logs.append(f"exit code: {rc}")

    return logs