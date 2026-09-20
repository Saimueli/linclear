from dataclasses import dataclass, field


def human_size(n: int) -> str:
    if not n or n < 0:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n); i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0; i += 1
    return f"{int(f)} {units[i]}" if i == 0 else f"{f:.1f} {units[i]}"


@dataclass
class AppInfo:
    name: str
    package_id: str
    version: str = ""
    source: str = ""
    size_bytes: int = 0
    install_path: str = ""
    description: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def size_human(self) -> str:
        return human_size(self.size_bytes)


@dataclass
class LeftoverItem:
    path: str
    kind: str = "file"          # file | dir | symlink | command
    size_bytes: int = 0
    reason: str = ""
    selected: bool = True
    category: str = ""

    @property
    def size_human(self) -> str:
        return human_size(self.size_bytes)