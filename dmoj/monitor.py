import logging
from contextlib import closing
from threading import Event, Thread
from urllib.request import urlopen

from dmoj import judgeenv
from dmoj.judgeenv import get_problem_watches, startup_warnings
from dmoj.utils.ansi import print_ansi
from dmoj.utils.glob_ext import find_glob_root

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    has_watchdog_installed = True
except ImportError:
    startup_warnings.append('watchdog module not found, install it to automatically update problems')
    has_watchdog_installed = False

logger = logging.getLogger(__name__)


class RefreshWorker(Thread):
    def __init__(self, urls):
        super().__init__()
        self.urls = urls
        self.daemon = True
        self._trigger = Event()
        self._terminate = False

    def refresh(self):
        self._trigger.set()

    def stop(self):
        self._terminate = True
        self._trigger.set()

    def run(self):
        while True:
            self._trigger.wait()
            self._trigger.clear()
            if self._terminate:
                break

            for url in self.urls:
                logger.info('Pinging for problem update: %s', url)
                try:
                    with closing(urlopen(url, data='')) as f:
                        f.read()
                except Exception:
                    logger.exception('Failed to ping for problem update: %s', url)


class SendProblemsHandler(FileSystemEventHandler):
    def __init__(self, refresher=None):
        self.refresher = refresher
        self.callback = None

    def on_any_event(self, event):
        if self.callback is not None:
            self.callback()
        if self.refresher is not None:
            self.refresher.refresh()


class Monitor:
    def __init__(self):
        if has_watchdog_installed and not judgeenv.no_watchdog:
            if judgeenv.env.update_pings:
                logger.info('Using thread to ping urls: %r', judgeenv.env.update_pings)
                self._refresher = RefreshWorker(judgeenv.env.update_pings)
            else:
                self._refresher = None

            self._handler = SendProblemsHandler(self._refresher)
            self._monitor = Observer()

            for dir in set(map(find_glob_root, get_problem_watches())):
                self._monitor.schedule(self._handler, dir, recursive=True)
                logger.info('Scheduled for monitoring: %s', dir)
        else:
            self._monitor = None
            self._refresher = None

    @property
    def is_real(self):
        return self._monitor is not None

    @property
    def callback(self):
        return self._handler.callback

    @callback.setter
    def callback(self, callback):
        if self._monitor is not None:
            self._handler.callback = callback

    def start(self):
        if self._monitor is not None:
            try:
                self._monitor.start()
            except OSError:
                logger.exception('Failed to start problem monitor.')
                print_ansi('#ansi[Warning: failed to start problem monitor!](yellow)')
        if self._refresher is not None:
            self._refresher.start()

    def join(self):
        if self._monitor is not None:
            self._monitor.join()
        if self._refresher is not None:
            self._refresher.join()

    def stop(self):
        if self._refresher is not None:
            self._refresher.stop()
        if self._monitor is not None:
            self._monitor.stop()
            self._monitor.join(1)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
