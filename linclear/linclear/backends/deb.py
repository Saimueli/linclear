import shutil
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo, CAT_APP, CAT_LIB, CAT_SYS

# Debian sections that indicate a library or system package
_SYS_SECTIONS = {"admin", "base", "kernel", "libs", "libdevel", "oldlibs",
                 "devel", "debug", "doc", "metapackages", "shells"}

_LIB_PREFIXES = ("lib", "python3-", "python2-", "perl-", "ruby-", "php-",
                 "golang-", "node-", "java-")


def _classify(name: str, section: str, summary: str) -> str:
    n = name.lower()
    s = section.lower().strip()
    if s in ("libs", "libdevel", "oldlibs", "debug", "doc"):
        return CAT_LIB
    if s in ("admin", "base", "kernel", "devel", "metapackages"):
        return CAT_SYS
    if any(n.startswith(p) for p in _LIB_PREFIXES):
        return CAT_LIB
    if n.endswith(("-dev", "-dbg", "-dbgsym", "-doc", "-headers", "-common")):
        return CAT_LIB
    if "library" in summary.lower():
        return CAT_LIB
    return CAT_APP


class DebBackend(Backend):
    source_name = "DEB"
    command_name = "dpkg-query"

    def list_apps(self) -> List[AppInfo]:
        import subprocess
        fmt = (r"${Package}\t${Version}\t${Installed-Size}\t${Status}\t"
               r"${binary:Summary}\t${Section}\n")
        out = subprocess.run(
            ["dpkg-query", "-W", "-f=" + fmt],
            capture_output=True, text=True, check=False,
        ).stdout
        apps = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 6:
                continue
            name, version, size_kb, status, summary, section = parts[:6]
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
                category=_classify(name, section, summary),
                extra={"section": section},
            ))
        return apps

    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        if shutil.which("apt-get"):
            return [(["apt-get", "remove", "--purge", "-y", app.package_id], True)]
        return [(["dpkg", "-r", app.package_id], True)]
