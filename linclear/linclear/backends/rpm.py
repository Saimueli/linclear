import re
import shutil
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo, CAT_APP, CAT_LIB, CAT_SYS

# RPM groups that mean "system" rather than "user app"
_SYS_GROUPS = (
    "system environment/base", "system environment/libraries",
    "system environment/kernel", "system environment/daemons",
    "development/libraries", "development/system",
    "development/tools", "applications/system",
    "unspecified",
)

_LIB_PREFIXES = ("lib", "python3-", "python2-", "perl-", "ruby-", "php-",
                 "golang-", "nodejs-", "java-", "ghc-")

_LIB_SUFFIXES = ("-devel", "-dev", "-debug", "-doc", "-doc", "-headers",
                 "-libs", "-static", "-devel-debuginfo")


def _classify(name: str, group: str, summary: str) -> str:
    n = name.lower()
    g = group.lower().strip()
    if g in _SYS_GROUPS or g.startswith("system environment"):
        return CAT_SYS
    if any(n.startswith(p) for p in _LIB_PREFIXES):
        return CAT_LIB
    if any(n.endswith(s) for s in _LIB_SUFFIXES):
        return CAT_LIB
    s = summary.lower()
    if "library" in s and "libraries" not in s.split():
        return CAT_LIB
    if "library" in s:
        return CAT_LIB
    return CAT_APP


class RpmBackend(Backend):
    source_name = "RPM"
    command_name = "rpm"

    def list_apps(self) -> List[AppInfo]:
        import subprocess
        fmt = (r"%{NAME}\t%{VERSION}-%{RELEASE}\t%{SIZE}\t%{SUMMARY}\t"
               r"%{GROUP}\n")
        out = subprocess.run(
            ["rpm", "-qa", "--qf", fmt],
            capture_output=True, text=True, check=False,
        ).stdout
        apps = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            name, version, size_s, summary, group = parts[:5]
            try:
                size_i = int(size_s)
            except ValueError:
                size_i = 0
            apps.append(AppInfo(
                name=name, package_id=name, version=version,
                source=self.source_name, size_bytes=size_i,
                description=summary,
                category=_classify(name, group, summary),
                extra={"group": group},
            ))
        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        if shutil.which("dnf"):
            return [(["dnf", "remove", "-y", app.package_id], True)]
        return [(["rpm", "-e", app.package_id], True)]
