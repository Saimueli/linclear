from .rpm import RpmBackend
from .deb import DebBackend
from .snap import SnapBackend
from .flatpak import FlatpakBackend
from .manual import ManualBackend

ALL_BACKENDS = [RpmBackend, DebBackend, SnapBackend, FlatpakBackend, ManualBackend]


def get_backends():
    return [cls() for cls in ALL_BACKENDS]