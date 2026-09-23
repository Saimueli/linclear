"""Detects apps not tracked by any package manager."""
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional
from .base import Backend
from ..models import AppInfo, CAT_APP

HOME = Path.home()


def _file_owned_by_package(path: str) -> bool:
    is_dir = os.path.isdir(path)
    check = path + ("/" if is_dir and not path.endswith("/") else "")
    if shutil.which("dpkg"):
        r = subprocess.run(["dpkg", "-S", check], capture_output=True,
                           text=True, check=False)
        if r.returncode == 0:
            return True
    if shutil.which("rpm"):
        r = subprocess.run(["rpm", "-qf", path], capture_output=True,
                           text=True, check=False)
        if r.returncode == 0 and "not owned by any package" not in r.stdout:
            return True
    if shutil.which("pacman"):
        r = subprocess.run(["pacman", "-Qo", check], capture_output=True,
                           text=True, check=False)
        if r.returncode == 0:
            return True
    return False


def _parse_desktop(path: Path) -> Optional[dict]:
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    data = {"Name": None, "Exec": None, "Comment": None}
    in_entry = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            in_entry = (s == "[Desktop Entry]")
            continue
        if not in_entry or "=" not in s:
            continue
        k, v = s.split("=", 1)
        if k in data and data[k] is None:
            data[k] = v
    return data if data["Name"] else None


def _clean_exec(exec_line: str) -> str:
    exec_line = re.sub(r"%[fFuUdDnNickvm]", "", exec_line).strip()
    try:
        parts = shlex.split(exec_line)
    except ValueError:
        parts = exec_line.split()
    return parts[0] if parts else ""


class ManualBackend(Backend):
    source_name = "Manual"
    command_name = "sh"

    def is_available(self) -> bool:
        return True

    def list_apps(self) -> List[AppInfo]:
        apps: List[AppInfo] = []
        seen = set()

        for d in (HOME / ".local/share/applications",
                  Path("/usr/local/share/applications")):
            if not d.is_dir():
                continue
            for f in d.glob("*.desktop"):
                if str(f) in seen:
                    continue
                seen.add(str(f))
                data = _parse_desktop(f)
                if not data:
                    continue
                exec_line = data.get("Exec") or ""
                if "flatpak" in exec_line or "/snap/" in exec_line:
                    continue
                if _file_owned_by_package(str(f)):
                    continue
                exec_bin = _clean_exec(exec_line)
                target = (exec_bin if os.path.isabs(exec_bin)
                          else (shutil.which(exec_bin) or exec_bin))
                apps.append(AppInfo(
                    name=data["Name"], package_id=f.stem, source=self.source_name,
                    description=data.get("Comment") or "",
                    install_path=target or str(f),
                    category=CAT_APP,
                    extra={"desktop_file": str(f), "exec": exec_bin},
                ))

        opt = Path("/opt")
        if opt.is_dir():
            for child in opt.iterdir():
                if not child.is_dir():
                    continue
                if child.name == "AppImages":
                    continue  # handled by AppImage backend
                if _file_owned_by_package(str(child)):
                    continue
                apps.append(AppInfo(
                    name=child.name, package_id=child.name,
                    source=self.source_name, description="Directory in /opt",
                    install_path=str(child),
                    category=CAT_APP,
                    extra={"paths": [str(child)]},
                ))

        user_bin = HOME / ".local/bin"
        if user_bin.is_dir():
            for f in user_bin.iterdir():
                if not f.is_file() or not os.access(f, os.X_OK):
                    continue
                if f.name.endswith(".AppImage"):
                    continue  # AppImage backend handles these
                if str(f) in seen:
                    continue
                seen.add(str(f))
                apps.append(AppInfo(
                    name=f.name, package_id=f.name, source=self.source_name,
                    description="Executable in ~/.local/bin",
                    install_path=str(f),
                    category=CAT_APP,
                    extra={"paths": [str(f)]},
                ))

        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        paths = set()
        for p in (app.extra.get("paths") or []):
            if p and os.path.exists(p):
                paths.add(p)
        for p in (app.install_path, app.extra.get("desktop_file")):
            if p and os.path.exists(p):
                paths.add(p)
        if not paths:
            return []
        needs_root = any(not str(p).startswith(str(HOME)) for p in paths)
        return [(["rm", "-rf", "--", *sorted(paths)], needs_root)]
