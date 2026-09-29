"""Plain data containers used across the application."""

from dataclasses import dataclass, field
from typing import List


def human_size(n: int) -> str:
    """Format a byte count for humans."""
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "—"
    if n <= 0:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(n)
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(value)} {units[idx]}"
    return f"{value:.1f} {units[idx]}"


@dataclass
class AppInfo:
    """A single installed application."""

    name: str
    package: str = ""
    version: str = ""
    source: str = ""
    size: int = 0
    category: str = ""
    description: str = ""
    path: str = ""
    uninstall_cmd: List[str] = field(default_factory=list)
    needs_root: bool = True

    @property
    def size_str(self) -> str:
        return human_size(self.size)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.package or self.name}"


@dataclass
class LeftoverItem:
    """A file or directory left behind by an uninstalled application."""

    path: str
    kind: str = "file"          # file | dir | symlink
    size: int = 0
    needs_root: bool = False

    @property
    def size_str(self) -> str:
        return human_size(self.size)