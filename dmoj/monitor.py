from dmoj import judgeenv
from dmoj.judgeenv import startup_warnings, get_problem_roots

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    startup_warnings.append('watchdog module not found, install it to automatically update problems')
    Observer = None


class SendProblemsHandler(FileSystemEventHandler):
    def __init__(self):
        self.callback = None

    def on_any_event(self, event):
        if self.callback is not None:
            self.callback()


class Monitor(object):
    def __init__(self):
        if Observer is not None and not judgeenv.no_watchdog:
            self._handler = SendProblemsHandler()
            self._monitor = monitor = Observer()
            for dir in get_problem_roots():
                monitor.schedule(self._handler, dir, recursive=True)
            try:
                monitor.start()
            except OSError:
                startup_warnings.append('failed to start filesystem monitor')
                self._monitor = None
        else:
            self._monitor = None

    @property
    def callback(self):
        return self._handler.callback

    @callback.setter
    def callback(self, callback):
        self._handler.callback = callback

    def _stop_monitor(self):
        if self._monitor is not None:
            self._monitor.stop()
            self._monitor.join(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_monitor()
