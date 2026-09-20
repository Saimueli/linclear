import shutil
from abc import ABC, abstractmethod
from typing import Callable, List, Tuple
from ..models import AppInfo, LeftoverItem


class Backend(ABC):
    source_name = "base"
    command_name = ""

    def is_available(self) -> bool:
        return bool(shutil.which(self.command_name))

    @abstractmethod
    def list_apps(self) -> List[AppInfo]: ...

    @abstractmethod
    def plan_uninstall(self, app: AppInfo) -> List[Tuple[List[str], bool]]:
        """Return [(argv, needs_root), ...] showing exactly what will run."""

    def uninstall(self, app: AppInfo, emit: Callable[[str], None],
                  dry_run: bool = False) -> int:
        from ..privileged import run_command
        rc = 0
        for argv, needs_root in self.plan_uninstall(app):
            r = run_command(argv, emit=emit, privileged=needs_root, dry_run=dry_run)
            if r != 0:
                rc = r
        return rc

    def scan_leftovers(self, app: AppInfo, emit=None) -> List[LeftoverItem]:
        return []