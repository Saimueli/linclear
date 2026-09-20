"""Run commands, escalating privileges via pkexec (preferred) or a terminal."""
import os, shlex, shutil, subprocess

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


def _stream(argv, emit):
    if emit:
        emit("$ " + " ".join(shlex.quote(a) for a in argv))
    try:
        proc = subprocess.Popen(
            argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
    except FileNotFoundError as e:
        if emit:
            emit(f"[error] {e}")
        return 127
    for line in proc.stdout:
        if emit:
            emit(line.rstrip("\n"))
    return proc.wait()


def run_command(argv, emit=None, privileged=False, dry_run=False):
    if dry_run:
        prefix = "sudo " if privileged else ""
        if emit:
            emit(f"[dry-run] {prefix}{' '.join(shlex.quote(a) for a in argv)}")
        return 0

    if not privileged:
        return _stream(argv, emit)

    # resolve absolute path so pkexec's restricted PATH can still find it
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