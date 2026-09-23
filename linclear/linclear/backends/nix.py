"""NixOS / Nix profile backend.

Handles two CLI surfaces:
  * `nix profile list`  (new nix 2.4+ "nix" command)
  * `nix-env -q`        (legacy nix-env)

System packages installed via configuration.nix cannot be removed with a
single command — the GUI marks them and just tells the user what to edit.
"""
import os
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple
from .base import Backend
from ..models import AppInfo, CAT_APP, CAT_SYS

_STORE_PATH_RE = re.compile(r"^(/nix/store/[a-z0-9]{32})-(.+?)(?:-([\d][\w.\-+]*))?$")


def _strip_version(name_version: str) -> tuple[str, str]:
    """'firefox-128.0' -> ('firefox', '128.0')"""
    parts = name_version.rsplit("-", 1)
    if len(parts) == 2 and parts[1] and parts[1][0].isdigit():
        return parts[0], parts[1]
    return name_version, ""


def _size_of_store_path(path: str) -> int:
    """Query the size of a single store path in bytes."""
    try:
        r = subprocess.run(
            ["nix-store", "--query", "--size", path],
            capture_output=True, text=True, check=False, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip().isdigit():
            return int(r.stdout.strip())
    except Exception:
        pass
    return 0


class NixBackend(Backend):
    source_name = "Nix"
    command_name = "nix"

    def is_available(self) -> bool:
        return bool(shutil.which("nix") or shutil.which("nix-env"))

    # ------------------------------------------------------------ listing --
    def list_apps(self) -> List[AppInfo]:
        # Try the new nix CLI first
        if shutil.which("nix"):
            try:
                apps = self._list_via_nix_profile()
                if apps:
                    return apps
            except Exception:
                pass
        if shutil.which("nix-env"):
            return self._list_via_nix_env()
        return []

    def _list_via_nix_profile(self) -> List[AppInfo]:
        r = subprocess.run(
            ["nix", "profile", "list"],
            capture_output=True, text=True, check=False, timeout=15,
        )
        if r.returncode != 0:
            return []

        blocks: list[dict[str, str]] = []
        cur: dict[str, str] = {}
        for line in r.stdout.splitlines():
            if line.startswith("Index:"):
                if cur:
                    blocks.append(cur)
                cur = {}
            if ":" in line:
                k, v = line.split(":", 1)
                cur[k.strip()] = v.strip()
        if cur:
            blocks.append(cur)

        apps: List[AppInfo] = []
        store_paths: list[str] = []
        for b in blocks:
            attr = b.get("Flake attribute", "")
            store = b.get("Store paths", "")
            # Take the first store path if multiple
            first_store = store.split()[0] if store else ""
            display = attr.split(".")[-1] if attr else os.path.basename(first_store)
            name, version = _strip_version(display)
            apps.append(AppInfo(
                name=name,
                package_id=attr or first_store,
                version=version,
                source=self.source_name,
                category=CAT_APP,
                install_path=first_store,
                description=f"Nix profile package ({attr})",
                extra={"store_path": first_store, "attr": attr, "index": b.get("Index", "")},
            ))
            store_paths.append(first_store)

        # Fetch sizes in parallel (best-effort, 8 workers)
        self._fill_sizes(apps, store_paths)
        return apps

    def _list_via_nix_env(self) -> List[AppInfo]:
        r = subprocess.run(
            ["nix-env", "-q", "--out-path"],
            capture_output=True, text=True, check=False, timeout=15,
        )
        if r.returncode != 0:
            return []

        apps: List[AppInfo] = []
        store_paths: list[str] = []
        for line in r.stdout.splitlines():
            if not line.strip():
                continue
            # Format: "name-version  /nix/store/..."
            parts = line.split()
            if len(parts) < 2:
                continue
            name_ver, store = parts[0], parts[1]
            name, version = _strip_version(name_ver)
            apps.append(AppInfo(
                name=name,
                package_id=name_ver,
                version=version,
                source=self.source_name,
                category=CAT_APP,
                install_path=store,
                description=f"Nix profile package ({name_ver})",
                extra={"store_path": store},
            ))
            store_paths.append(store)

        self._fill_sizes(apps, store_paths)
        return apps

    @staticmethod
    def _fill_sizes(apps: List[AppInfo], store_paths: List[str]):
        if not store_paths:
            return
        with ThreadPoolExecutor(max_workers=8) as ex:
            sizes = list(ex.map(_size_of_store_path, store_paths))
        for a, sz in zip(apps, sizes):
            a.size_bytes = sz

    # --------------------------------------------------------- uninstall --
    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        attr = app.extra.get("attr", "")
        if shutil.which("nix") and attr:
            return [(["nix", "profile", "remove", attr], False)]
        # legacy fallback
        return [(["nix-env", "-e", app.package_id], False)]

    def scan_leftovers(self, app: AppInfo, emit=None) -> list:
        """Nix store cleanup: suggest gc after removal."""
        from ..models import LeftoverItem
        return [LeftoverItem(
            path="nix-collect-garbage",
            kind="command",
            reason="Remove unreferenced Nix store paths",
            category="Package cleanup",
        )]