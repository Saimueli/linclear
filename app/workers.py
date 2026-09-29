"""Background workers (QThread) used by the UI."""

import subprocess
from typing import Callable, List

from PyQt6.QtCore import QThread, pyqtSignal


class FunctionWorker(QThread):
    """Runs an arbitrary callable in a background thread."""

    done = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn: Callable, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # pragma: no cover - defensive
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            return
        self.done.emit(result)


class CommandWorker(QThread):
    """Streams the output of an external command line by line."""

    line = pyqtSignal(str)
    finished_rc = pyqtSignal(int)

    def __init__(self, cmd: List[str], parent=None):
        super().__init__(parent)
        self.cmd = list(cmd)

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                errors="replace",
                bufsize=1,
            )
        except Exception as exc:
            self.line.emit(f"failed to start command: {exc}")
            self.finished_rc.emit(127)
            return

        try:
            if proc.stdout is not None:
                for raw in proc.stdout:
                    self.line.emit(raw.rstrip("\n"))
        except Exception:
            pass

        proc.wait()
        self.finished_rc.emit(proc.returncode)