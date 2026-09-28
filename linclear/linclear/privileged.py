import os
import shlex
import shutil
import subprocess
from typing import Callable, List, Optional


def _clean_env() -> dict:
    env = dict(os.environ)
    for var in ["LD_LIBRARY_PATH", "PYTHONHOME", "PYTHONPATH"]:
        env.pop(var, None)

    if "LD_LIBRARY_PATH_ORIG" in env:
        env["LD_LIBRARY_PATH"] = env.pop("LD_LIBRARY_PATH_ORIG")

    return env


TERMINALS = [
    ("x-terminal-emulator", ["-e"]),
    ("gnome-terminal",      ["--"]),
    ("konsole",             ["-e"]),
    ("xfce4-terminal",      ["-e"]),
    ("xterm",               ["-e"]),
]


def _find_terminal():
    for name, args in TERMINALS:
        path = shutil.which(name)
        if path:
            return path, args
    return None, None


def _stream(argv: List[str], emit: Optional[Callable[[str], None]]) -> int:
    if emit:
        emit("$ " + " ".join(shlex.quote(a) for a in argv))
    try:
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=_clean_env(),
        )
    except FileNotFoundError as e:
        if emit:
            emit(f"[error] {e}")
        return 127
    if proc.stdout:
        for line in proc.stdout:
            if emit:
                emit(line.rstrip("\n"))
    return proc.wait()


def run_command(argv: List[str], emit: Optional[Callable[[str], None]] = None,
                privileged: bool = False, dry_run: bool = False) -> int:
    if dry_run:
        prefix = "sudo " if privileged else ""
        if emit:
            emit(f"[dry-run] {prefix}{' '.join(shlex.quote(a) for a in argv)}")
        return 0

    if not privileged:
        return _stream(argv, emit)

    if argv and not os.path.isabs(argv[0]):
        resolved = shutil.which(argv[0])
        if resolved:
            argv = [resolved, *argv[1:]]

    pkexec = shutil.which("pkexec")
    if pkexec:
        return _stream([pkexec, *argv], emit)

    term, term_args = _find_terminal()
    if not term:
        msg = "No pkexec or terminal emulator found — cannot escalate privileges."
        if emit:
            emit(f"[error] {msg}")
        raise RuntimeError(msg)

    shell_cmd = "sudo " + " ".join(shlex.quote(a) for a in argv)
    wrapper = f"{shell_cmd}; echo; echo '[Linclear] Command finished. Press Enter.'; read _"
    return _stream([term, *term_args, "bash", "-c", wrapper], emit)
