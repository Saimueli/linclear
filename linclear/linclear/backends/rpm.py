import shutil
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo


class RpmBackend(Backend):
    source_name = "RPM"
    command_name = "rpm"

    def list_apps(self) -> List[AppInfo]:
        import subprocess
        fmt = r"%{NAME}\t%{VERSION}-%{RELEASE}\t%{SIZE}\t%{SUMMARY}\n"
        out = subprocess.run(
            ["rpm", "-qa", "--qf", fmt],
            capture_output=True, text=True, check=False,
        ).stdout
        apps = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            name, version, size_s, summary = parts[0], parts[1], parts[2], parts[3]
            try:
                size_i = int(size_s)
            except ValueError:
                size_i = 0
            apps.append(AppInfo(
                name=name, package_id=name, version=version,
                source=self.source_name, size_bytes=size_i,
                description=summary,
            ))
        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        if shutil.which("dnf"):
            return [(["dnf", "remove", "-y", app.package_id], True)]
        return [(["rpm", "-e", app.package_id], True)]