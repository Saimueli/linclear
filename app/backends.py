"""All application-discovery backends, in one file on purpose."""

import os
import re
import subprocess
from typing import Callable, List, Tuple

from . import privileged
from .models import AppInfo

HOME = os.path.expanduser("~")


# --------------------------------------------------------------------- utils

def _run(cmd, timeout: int = 90) -> str:
    return privileged.run_capture(cmd, timeout=timeout)


_SIZE_RE = re.compile(r"([\d.,]+)\s*([KMGTP]?i?B)\b", re.IGNORECASE)
_SIZE_UNITS = {
    "B": 1,
    "KB": 1000, "MB": 1000 ** 2, "GB": 1000 ** 3, "TB": 1000 ** 4,
    "KIB": 1024, "MIB": 1024 ** 2, "GIB": 1024 ** 3, "TIB": 1024 ** 4,
}


def parse_size(text: str) -> int:
    m = _SIZE_RE.search(text or "")
    if not m:
        return 0
    try:
        value = float(m.group(1).replace(",", "."))
    except ValueError:
        return 0
    unit = m.group(2).upper()
    return int(value * _SIZE_UNITS.get(unit, 1))


def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


# --------------------------------------------------------------------- DEB

def list_deb() -> List[AppInfo]:
    if not privileged.which("dpkg-query"):
        return []

    fmt = ("${Package}\\t${Version}\\t${Installed-Size}\\t"
           "${Section}\\t${binary:Summary}\\n")
    out = _run(["dpkg-query", "-W", "-f=" + fmt], timeout=120)

    if privileged.which("apt-get"):
        remove = ["apt-get", "remove", "-y"]
    elif privileged.which("apt"):
        remove = ["apt", "remove", "-y"]
    else:
        remove = ["dpkg", "--purge"]

    apps: List[AppInfo] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        pkg, ver, size_kb, section, summary = parts[0], parts[1], parts[2], parts[3], parts[4]
        try:
            size = int(size_kb) * 1024
        except ValueError:
            size = 0
        apps.append(AppInfo(
            name=pkg,
            package=pkg,
            version=ver,
            source="DEB",
            size=size,
            category=(section.split("/")[-1] if section else "misc") or "misc",
            description=summary,
            needs_root=True,
            uninstall_cmd=remove + [pkg],
        ))
    return apps


# --------------------------------------------------------------------- RPM

def list_rpm() -> List[AppInfo]:
    if not privileged.which("rpm"):
        return []

    fmt = "%{NAME}\\t%{VERSION}-%{RELEASE}\\t%{SIZE}\\t%{GROUP}\\t%{SUMMARY}\\n"
    out = _run(["rpm", "-qa", "--queryformat", fmt], timeout=120)

    if privileged.which("dnf"):
        remove = ["dnf", "remove", "-y"]
    elif privileged.which("yum"):
        remove = ["yum", "remove", "-y"]
    else:
        remove = ["rpm", "-e", "--nodeps"]

    apps: List[AppInfo] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        name, ver, size_s, group, summary = parts[0], parts[1], parts[2], parts[3], parts[4]
        try:
            size = int(size_s)
        except ValueError:
            size = 0
        if group in ("(none)", "Unspecified", ""):
            group = "misc"
        apps.append(AppInfo(
            name=name,
            package=name,
            version=ver,
            source="RPM",
            size=size,
            category=group,
            description=summary,
            needs_root=True,
            uninstall_cmd=remove + [name],
        ))
    return apps


# --------------------------------------------------------------------- Pacman

def _pacman_block(block: dict) -> AppInfo:
    name = block.get("Name", "")
    return AppInfo(
        name=name,
        package=name,
        version=block.get("Version", ""),
        source="Pacman",
        size=parse_size(block.get("Installed Size", "")),
        category=block.get("Groups", "misc") or "misc",
        description=block.get("Description", ""),
        needs_root=True,
        uninstall_cmd=["pacman", "-Rns", "--noconfirm", name],
    )


def list_pacman() -> List[AppInfo]:
    if not privileged.which("pacman"):
        return []

    out = _run(["pacman", "-Qi"], timeout=120)
    apps: List[AppInfo] = []
    block: dict = {}

    for line in out.splitlines():
        if not line.strip():
            if block.get("Name"):
                apps.append(_pacman_block(block))
            block = {}
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            block[key.strip()] = value.strip()

    if block.get("Name"):
        apps.append(_pacman_block(block))
    return apps


# --------------------------------------------------------------------- Snap

def list_snap() -> List[AppInfo]:
    if not privileged.which("snap"):
        return []

    out = _run(["snap", "list"], timeout=60)
    apps: List[AppInfo] = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        name, ver = parts[0], parts[1]
        if name.lower() == "name":
            continue
        apps.append(AppInfo(
            name=name,
            package=name,
            version=ver,
            source="Snap",
            size=0,
            category="snap",
            description="Snap package",
            needs_root=True,
            uninstall_cmd=["snap", "remove", name],
        ))
    return apps


# --------------------------------------------------------------------- Flatpak

def list_flatpak() -> List[AppInfo]:
    if not privileged.which("flatpak"):
        return []

    out = _run(
        ["flatpak", "list", "--app",
         "--columns=name,application,version,size,origin"],
        timeout=90,
    )
    with_size = bool(out.strip())
    if not with_size:
        out = _run(
            ["flatpak", "list", "--app",
             "--columns=name,application,version,origin"],
            timeout=90,
        )
    if not out.strip():
        return []

    apps: List[AppInfo] = []
    for line in out.splitlines():
        parts = line.split("\t")
        if with_size:
            if len(parts) < 5:
                continue
            name, appid, ver, size_s, origin = parts[:5]
            size = parse_size(size_s)
        else:
            if len(parts) < 4:
                continue
            name, appid, ver, origin = parts[:4]
            size = 0
        apps.append(AppInfo(
            name=name or appid,
            package=appid,
            version=ver,
            source="Flatpak",
            size=size,
            category="flatpak",
            description=f"Flatpak application ({origin})" if origin else "Flatpak application",
            needs_root=False,
            uninstall_cmd=["flatpak", "uninstall", "-y", appid],
        ))
    return apps


# --------------------------------------------------------------------- AppImage

APPIMAGE_QUICK_DIRS = (
    "~/Applications",
    "~/AppImages",
    "~/.local/bin",
    "~/bin",
    "~/Downloads",
    "~/Desktop",
    "/opt",
    "/usr/local/bin",
    "/usr/local/Applications",
)


def _strip_appimage_suffix(name: str) -> str:
    low = name.lower()
    if low.endswith(".appimage"):
        return name[: -len(".AppImage")]
    return name


def appimage_info(path: str) -> AppInfo:
    base = os.path.basename(path)
    name = _strip_appimage_suffix(base) or base
    needs_root = path.startswith("/opt") or path.startswith("/usr")
    return AppInfo(
        name=name,
        package=base,
        version="",
        source="AppImage",
        size=_file_size(path),
        category="appimage",
        description=path,
        path=path,
        needs_root=needs_root,
        uninstall_cmd=["rm", "-f", path],
    )


def list_appimage() -> List[AppInfo]:
    found = set()
    for raw in APPIMAGE_QUICK_DIRS:
        directory = os.path.expanduser(raw)
        if not os.path.isdir(directory):
            continue
        try:
            with os.scandir(directory) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False) and entry.name.lower().endswith(".appimage"):
                        found.add(entry.path)
        except OSError:
            continue
    return [appimage_info(p) for p in sorted(found)]


def find_appimages_deep(timeout: int = 120) -> List[str]:
    """Deep scan for AppImages in HOME, /opt, /usr/local and /usr/share (depth 6)."""
    roots = [HOME, "/opt", "/usr/local", "/usr/share"]
    found = set()
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            proc = subprocess.run(
                ["find", root, "-maxdepth", "6", "-type", "f",
                 "-iname", "*.AppImage", "-print"],
                capture_output=True, text=True, timeout=timeout, errors="replace",
            )
        except Exception:
            continue
        for line in (proc.stdout or "").splitlines():
            line = line.strip()
            if line:
                found.add(line)
    return sorted(found)


# --------------------------------------------------------------------- Manual

def _dpkg_owned_desktop_files() -> set:
    if not privileged.which("dpkg-query"):
        return set()
    owned = set()
    for pattern in ("/usr/share/applications/*", "/usr/local/share/applications/*"):
        out = _run(["dpkg-query", "-S", pattern], timeout=90)
        for line in out.splitlines():
            if ":" in line:
                owned.add(line.split(":", 1)[1].strip())
    return owned


def _parse_desktop(path: str):
    name = comment = categories = exec_line = icon = ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            in_entry = False
            for raw in handle:
                line = raw.rstrip("\n")
                if line.startswith("["):
                    in_entry = line.strip() == "[Desktop Entry]"
                    continue
                if not in_entry or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key == "Name" and not name:
                    name = value
                elif key == "Comment" and not comment:
                    comment = value
                elif key == "Categories" and not categories:
                    categories = value
                elif key == "Exec" and not exec_line:
                    exec_line = value
                elif key == "Icon" and not icon:
                    icon = value
                elif key == "NoDisplay" and value.lower() == "true":
                    return None
    except OSError:
        return None
    if not name:
        return None
    return name, comment, categories, exec_line, icon


def list_manual() -> List[AppInfo]:
    """.desktop files that do not belong to any package manager."""
    has_deb = privileged.which("dpkg-query") is not None

    dirs = [
        os.path.join(HOME, ".local", "share", "applications"),
        "/usr/local/share/applications",
    ]
    if has_deb:
        # Only scan the system directory when we can tell what is packaged.
        dirs.append("/usr/share/applications")

    owned = _dpkg_owned_desktop_files()
    apps: List[AppInfo] = []
    seen = set()

    for directory in dirs:
        if not os.path.isdir(directory):
            continue
        try:
            entries = sorted(os.listdir(directory))
        except OSError:
            continue
        for entry in entries:
            if not entry.endswith(".desktop"):
                continue
            path = os.path.join(directory, entry)
            if path in owned or path in seen:
                continue
            seen.add(path)
            parsed = _parse_desktop(path)
            if not parsed:
                continue
            name, comment, categories, _exec_line, _icon = parsed
            needs_root = not path.startswith(HOME)
            apps.append(AppInfo(
                name=name,
                package=entry[:-len(".desktop")],
                version="",
                source="Manual",
                size=_file_size(path),
                category=(categories.split(";")[0] if categories else "desktop") or "desktop",
                description=comment or path,
                path=path,
                needs_root=needs_root,
                uninstall_cmd=["rm", "-f", path],
            ))
    return apps


# --------------------------------------------------------------------- registry

BACKENDS: List[Tuple[str, Callable[[], List[AppInfo]]]] = [
    ("DEB", list_deb),
    ("RPM", list_rpm),
    ("Pacman", list_pacman),
    ("Snap", list_snap),
    ("Flatpak", list_flatpak),
    ("AppImage", list_appimage),
    ("Manual", list_manual),
]

SOURCE_NAMES = [name for name, _ in BACKENDS]