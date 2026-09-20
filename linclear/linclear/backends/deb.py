import shutil
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo


class DebBackend(Backend):
    source_name = "DEB"
    command_name = "dpkg-query"

    def list_apps(self) -> List[AppInfo]:
        import subprocess
        fmt = (r"${Package}\t${Version}\t${Installed-Size}\t${Status}\t"
               r"${binary:Summary}\n")
        out = subprocess.run(
            ["dpkg-query", "-W", "-f=" + fmt],
            capture_output=True, text=True, check=False,
        ).stdout
        apps = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            name, version, size_kb, status, summary = parts[:5]
            if "installed" not in status:
                continue
            try:
                size_i = int(size_kb) * 1024
            except ValueError:
                size_i = 0
            apps.append(AppInfo(
                name=name, package_id=name, version=version,
                source=self.source_name, size_bytes=size_i,
                description=summary,
            ))
        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        if shutil.which("apt-get"):
            return [(["apt-get", "remove", "--purge", "-y", app.package_id], True)]
        return [(["dpkg", "-r", app.package_id], True)]