import subprocess
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo, CAT_APP


def _parse_size(s: str) -> int:
    parts = s.strip().split()
    if len(parts) != 2:
        return 0
    try:
        val = float(parts[0])
    except ValueError:
        return 0
    mult = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    return int(val * mult.get(parts[1].upper(), 1))


class FlatpakBackend(Backend):
    source_name = "Flatpak"
    command_name = "flatpak"

    def list_apps(self) -> List[AppInfo]:
        cols = "application,name,version,size,origin,installation"
        r = subprocess.run(
            ["flatpak", "list", "--app", f"--columns={cols}"],
            capture_output=True, text=True, check=False,
        )
        if r.returncode != 0:
            cols = "application,name,version,size,origin"
            r = subprocess.run(
                ["flatpak", "list", "--app", f"--columns={cols}"],
                capture_output=True, text=True, check=False,
            )
        apps = []
        for line in r.stdout.splitlines():
            if not line.strip():
                continue
            c = line.split("\t")
            if len(c) < 5:
                continue
            app_id, name, version, size_s, origin = c[:5]
            install = c[5] if len(c) > 5 else ""
            apps.append(AppInfo(
                name=name or app_id, package_id=app_id, version=version,
                source=self.source_name, size_bytes=_parse_size(size_s),
                description=f"Flatpak ({origin}{', ' + install if install else ''})",
                install_path=f"/var/lib/flatpak/app/{app_id}",
                category=CAT_APP,
                extra={"origin": origin, "installation": install},
            ))
        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        install = app.extra.get("installation", "")
        argv = ["flatpak", "uninstall", "-y"]
        if install:
            argv += [f"--{install}"]
        argv.append(app.package_id)
        return [(argv, install != "user")]
