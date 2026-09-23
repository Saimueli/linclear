from .rpm import RpmBackend
from .deb import DebBackend
from .pacman import PacmanBackend
from .snap import SnapBackend
from .flatpak import FlatpakBackend
from .nix import NixBackend
from .manual import ManualBackend
from .appimage import AppImageBackend

ALL_BACKENDS = [
    RpmBackend,
    DebBackend,
    PacmanBackend,
    SnapBackend,
    FlatpakBackend,
    NixBackend,
    ManualBackend,
    AppImageBackend,
]


def get_backends():
    return [cls() for cls in ALL_BACKENDS]
