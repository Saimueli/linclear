"""Whitelist/blacklist protection for system-critical packages."""

CRITICAL_PACKAGES = {
    # init / core
    "systemd", "sysvinit", "init", "upstart", "base", "base-devel",
    # libc / toolchain
    "glibc", "libc6", "libc-bin", "libc-dev-bin", "libgcc", "libgcc-s1",
    "libstdc++", "libstdc++6", "gcc", "gcc-libs", "binutils",
    # package managers — removing these bricks the system
    "dnf", "rpm", "yum", "apt", "dpkg", "apt-utils", "snapd", "flatpak",
    "pacman", "nix", "nix-env", "nix-store",
    # shells / coreutils
    "bash", "coreutils", "util-linux", "bash-completion", "zsh", "fish",
    # kernels
    "kernel", "kernel-core", "kernel-modules", "linux",
    "linux-image-generic", "linux-image-amd64", "linux-lts", "linux-zen",
    # boot
    "grub2", "grub-common", "grub2-common", "grub", "efibootmgr", "os-prober",
    # filesystems / storage
    "filesystem", "e2fsprogs", "xfsprogs", "btrfs-progs", "lvm2",
    "cryptsetup", "mdadm",
    # ssh / crypto
    "openssh-server", "openssh-client", "openssl", "ca-certificates",
    # auth
    "pam", "libpam0g", "libpam-runtime", "shadow", "sudo",
    # display servers / desktops
    "xorg-x11-server-Xorg", "xserver-xorg", "xserver-xorg-core",
    "gnome-shell", "gdm", "gdm3", "sddm", "lightdm", "plasma-desktop",
    # python runtime
    "python3", "python3-minimal", "python3.11", "python3.12", "python3.13",
    "python3.11-minimal", "python3.12-minimal", "python3.13-minimal",
    # firmware / drivers
    "linux-firmware", "mesa-dri-drivers", "mesa-vulkan-drivers",
    "nvidia", "nvidia-utils",
    # security
    "selinux-policy", "selinux-policy-targeted", "firewalld", "ufw",
    # Arch groups that shouldn't be touched
    "linux-api-headers", "tzdata", "iana-etc", "mkinitcpio", "hwids",
}

CRITICAL_PREFIXES = (
    "kernel-", "linux-image-", "linux-headers-", "linux-modules-",
    "linux-firmware-", "grub", "systemd-", "libc", "glibc",
    "nvidia-", "nixos-",
)


def is_critical(package_id: str) -> bool:
    pid = package_id.lower().strip()
    if pid in CRITICAL_PACKAGES:
        return True
    return any(pid.startswith(p) for p in CRITICAL_PREFIXES)
