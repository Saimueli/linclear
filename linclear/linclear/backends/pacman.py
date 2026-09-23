"""Arch Linux / Manjaro / EndeavourOS / CachyOS — pacman backend."""
import re
import shutil
import subprocess
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo, CAT_APP, CAT_LIB, CAT_SYS

_SIZE_UNITS = {
    "B":   1,
    "KIB": 1024, "MIB": 1024**2, "GIB": 1024**3, "TIB": 1024**4,
    "KB":  1024, "MB":  1024**2, "GB":  1024**3, "TB":  1024**4,
}

# Groups that indicate a system / dev package rather than a user app
_SYSTEM_GROUPS = {"base", "base-devel", "xorg", "xorg-apps", "xorg-fonts",
                  "linux", "linux-firmware", "realtime", "gnome", "kde-applications"}

# Package name prefixes that are almost always libraries
_LIB_PREFIXES = ("lib", "python-", "python2-", "python3-", "perl-", "ruby-",
                 "lua-", "haskell-", "php-", "gcc-", "clang-")


def _parse_size(s: str) -> int:
    """Parse '258.45 MiB' -> bytes."""
    m = re.match(r"^\s*([\d.]+)\s*([A-Za-z]+)\s*$", s)
    if not m:
        return 0
    try:
        val = float(m.group(1))
    except ValueError:
        return 0
    return int(val * _SIZE_UNITS.get(m.group(2).upper(), 1))


def _classify(name: str, groups: str, reason: str, desc: str) -> str:
    """Decide whether a pacman package is an application, library, or system package."""
    gset = {g.strip().lower() for g in groups.split() if g.strip()}
    if gset & _SYSTEM_GROUPS:
        return CAT_SYS
    if "base" in gset or "base-devel" in gset:
        return CAT_SYS
    # explicitly installed by the user -> likely an application
    if reason.lower().startswith("explicit"):
        # but still filter obvious libraries
        n = name.lower()
        if any(n.startswith(p) for p in _LIB_PREFIXES):
            return CAT_LIB
        if n.endswith(("-dev", "-debug", "-doc", "-headers", "-libs")):
            return CAT_LIB
        return CAT_APP
    # installed as dependency
    n = name.lower()
    if any(n.startswith(p) for p in _LIB_PREFIXES):
        return CAT_LIB
    if n.endswith(("-dev", "-debug", "-doc", "-headers", "-libs")):
        return CAT_LIB
    if "library" in desc.lower():
        return CAT_LIB
    return CAT_LIB  # dependencies default to library


class PacmanBackend(Backend):
    source_name = "Pacman"
    command_name = "pacman"

    def list_apps(self) -> List[AppInfo]:
        r = subprocess.run(
            ["pacman", "-Qi"],
            capture_output=True, text=True, check=False,
            env={"LC_ALL": "C.UTF-8", "PATH": "/usr/bin:/bin"},
        )
        if r.returncode != 0:
            return []

        apps: List[AppInfo] = []
        block: dict[str, str] = {}

        def flush():
            if not block:
                return
            name = block.get("Name", "").strip()
            if not name:
                return
            version = block.get("Version", "").strip()
            desc    = block.get("Description", "").strip()
            groups  = block.get("Groups", "").strip()
            reason  = block.get("Install Reason", "").strip()
            size    = _parse_size(block.get("Installed Size", ""))
            apps.append(AppInfo(
                name=name,
                package_id=name,
                version=version,
                source=self.source_name,
                size_bytes=size,
                description=desc,
                category=_classify(name, groups, reason, desc),
                install_path=f"/var/lib/pacman/local/{name}-{version}",
                extra={"groups": groups, "reason": reason},
            ))

        for line in r.stdout.splitlines():
            if not line.strip():
                flush()
                block = {}
                continue
            if ":" in line:
                k, v = line.split(":", 1)
                block[k.strip()] = v.strip()
        flush()

        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        # -Rns: remove package + its deps + system config files that are unmodified
        return [(["pacman", "-Rns", "--noconfirm", app.package_id], True)]