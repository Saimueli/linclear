import shutil, subprocess
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo


class SnapBackend(Backend):
    source_name = "Snap"
    command_name = "snap"

    def is_available(self) -> bool:
        if not shutil.which("snap"):
            return False
        r = subprocess.run(["snap", "list"], capture_output=True, text=True, check=False)
        return r.returncode == 0

    def list_apps(self) -> List[AppInfo]:
        r = subprocess.run(["snap", "list"], capture_output=True, text=True, check=False)
        apps = []
        for line in r.stdout.splitlines()[1:]:
            if not line.strip() or line.startswith("No snaps"):
                continue
            cols = line.split()
            if len(cols) < 3:
                continue
            name, version = cols[0], cols[1]
            notes = " ".join(cols[5:]) if len(cols) > 5 else ""
            apps.append(AppInfo(
                name=name, package_id=name, version=version,
                source=self.source_name, description=notes,
                install_path=f"/snap/{name}",
            ))
        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        return [(["snap", "remove", app.package_id], True)]