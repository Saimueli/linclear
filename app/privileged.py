"""Helpers for running commands, elevating privileges and streaming output."""

import os
import shlex
import shutil
import subprocess
from typing import List, Optional, Tuple

TERMINALS = ("gnome-terminal", "konsole", "xfce4-terminal", "xterm")

_APT_ENV = ["env", "DEBIAN_FRONTEND=noninteractive"]


# --------------------------------------------------------------------- utils

def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def has_pkexec() -> bool:
    return shutil.which("pkexec") is not None


def display(cmd: List[str]) -> str:
    """Shell-quoted, human readable representation of a command."""
    if not cmd:
        return ""
    return " ".join(shlex.quote(str(c)) for c in cmd)


def run(cmd: List[str], timeout: int = 120) -> Tuple[int, str, str]:
    """Run a command synchronously. Never raises."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            errors="replace",
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except FileNotFoundError as exc:
        return 127, "", str(exc)
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"
    except Exception as exc:  # pragma: no cover - defensive
        return 1, "", f"{type(exc).__name__}: {exc}"


def run_capture(cmd: List[str], timeout: int = 60) -> str:
    """Run a command and return stdout, or '' on any failure."""
    rc, out, _ = run(cmd, timeout=timeout)
    if rc != 0:
        return ""
    return out


# --------------------------------------------------------------------- root

def privileged_command(cmd: List[str]) -> List[str]:
    """Wrap *cmd* so it runs as root through pkexec (best effort)."""
    if has_pkexec():
        return ["pkexec"] + _APT_ENV + list(cmd)
    return list(cmd)


def terminal_command(cmd: List[str]) -> Optional[List[str]]:
    """Return argv that opens a terminal running `sudo <cmd>`.

    Returns None when no supported terminal emulator is installed.
    """
    script = "sudo " + display(cmd)
    script += '; echo; printf "Press Enter to close..."; read _'

    for term in TERMINALS:
        path = shutil.which(term)
        if not path:
            continue
        if term == "gnome-terminal":
            return [path, "--wait", "--", "bash", "-c", script]
        if term == "konsole":
            return [path, "--hold", "-e", "bash", "-c", script]
        if term == "xfce4-terminal":
            return [path, "--hold", "-e", "bash -c " + shlex.quote(script)]
        if term == "xterm":
            return [path, "-hold", "-e", "bash", "-c", script]
    return None


def effective_command(cmd: List[str], needs_root: bool) -> Optional[List[str]]:
    """Build the command that will actually be executed."""
    if not cmd:
        return None
    cmd = list(cmd)
    if not needs_root:
        return cmd
    if has_pkexec():
        return ["pkexec"] + _APT_ENV + cmd
    term = terminal_command(cmd)
    if term is not None:
        return term
    return None


def is_elevated_available() -> bool:
    return has_pkexec() or any(shutil.which(t) for t in TERMINALS)