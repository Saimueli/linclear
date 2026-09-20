from PyQt6.QtCore import QThread, pyqtSignal


class ListAppsWorker(QThread):
    output = pyqtSignal(str)
    done   = pyqtSignal(list)

    def __init__(self, backends):
        super().__init__()
        self.backends = backends

    def run(self):
        apps = []
        for b in self.backends:
            try:
                if not b.is_available():
                    self.output.emit(f"[skip] {b.source_name}: not available")
                    continue
            except Exception as e:
                self.output.emit(f"[skip] {b.source_name}: {e}")
                continue
            self.output.emit(f"[scan] {b.source_name}")
            try:
                found = b.list_apps()
                apps.extend(found)
                self.output.emit(f"[ok]   {b.source_name}: {len(found)} apps")
            except Exception as e:
                self.output.emit(f"[err]  {b.source_name}: {e}")
        self.done.emit(apps)


class CommandWorker(QThread):
    output = pyqtSignal(str)
    done   = pyqtSignal(int)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn  # callable(emit) -> int

    def run(self):
        try:
            rc = self.fn(self.output.emit)
        except Exception as e:
            self.output.emit(f"[error] {e}")
            rc = 1
        self.done.emit(rc)