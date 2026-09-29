"""Blacklist of packages that must never be removed."""

CRITICAL_NAMES = {
    "systemd", "systemd-sysv", "systemd-boot",
    "libc6", "libc-bin", "glibc", "glibc-common", "glibc-langpack-en",
    "bash", "coreutils", "util-linux", "passwd", "login", "shadow",
    "apt", "apt-get", "dpkg", "dnf", "rpm", "yum", "pacman", "zypper",
    "snapd", "flatpak", "sudo", "pkexec", "polkit", "polkitd",
    "python3", "python3-minimal", "python3.11", "python3.12",
    "openssh-server", "openssh-client",
    "grub", "grub2", "grub2-common", "grub-pc", "grub-efi", "grub-efi-amd64",
    "init", "initscripts", "kernel", "linux",
    "xorg-server", "xorg", "xserver-xorg", "gnome-shell",
    "dbus", "dbus-daemon", "udev", "e2fsprogs", "mount",
}

CRITICAL_PREFIXES = (
    "kernel-",
    "linux-image-",
    "linux-headers-",
    "linux-modules-",
    "linux-generic",
    "linux-firmware",
    "grub-",
    "systemd-",
    "libc6-",
    "xorg-server-",
    "xserver-xorg-",
    "initramfs-",
    "glibc-",
)


def is_critical(name: str) -> bool:
    """Return True when *name* refers to a protected system component."""
    if not name:
        return False
    base = name.strip().lower().split(":")[0]
    if base in CRITICAL_NAMES:
        return True
    for prefix in CRITICAL_PREFIXES:
        if base.startswith(prefix):
            return True
    return False


def critical_reason(name: str) -> str:
    return f"'{name}' is a protected system package and cannot be removed by Linclear."