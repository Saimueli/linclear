"""Whitelist/blacklist protection for system-critical packages."""

CRITICAL_PACKAGES = {
    "systemd", "sysvinit", "init", "upstart",
    "glibc", "libc6", "libc-bin", "libc-dev-bin", "libgcc", "libgcc-s1",
    "libstdc++", "libstdc++6", "gcc", "gcc-libs",
    "dnf", "rpm", "yum", "apt", "dpkg", "apt-utils", "snapd", "flatpak",
    "bash", "coreutils", "util-linux", "bash-completion", "zsh", "fish",
    "kernel", "kernel-core", "kernel-modules", "linux-image-generic",
    "linux-image-amd64", "grub2", "grub-common", "grub2-common",
    "filesystem", "e2fsprogs", "xfsprogs", "btrfs-progs", "lvm2",
    "openssh-server", "openssh-client", "openssl", "ca-certificates",
    "pam", "libpam0g", "libpam-runtime",
    "xorg-x11-server-Xorg", "xserver-xorg", "xserver-xorg-core",
    "gnome-shell", "gdm", "gdm3", "sddm", "lightdm", "plasma-desktop",
    "python3", "python3-minimal", "python3.11", "python3.12",
    "python3.11-minimal", "python3.12-minimal",
    "linux-firmware", "mesa-dri-drivers", "mesa-vulkan-drivers",
    "selinux-policy", "selinux-policy-targeted", "firewalld", "ufw",
}

CRITICAL_PREFIXES = (
    "kernel-", "linux-image-", "linux-headers-", "linux-modules-",
    "grub", "systemd-", "libc", "glibc",
)


def is_critical(package_id: str) -> bool:
    pid = package_id.lower().strip()
    if pid in CRITICAL_PACKAGES:
        return True
    return any(pid.startswith(p) for p in CRITICAL_PREFIXES)