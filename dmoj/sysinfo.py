import os
from multiprocessing import cpu_count

_cpu_count = cpu_count()


if hasattr(os, 'getloadavg'):
    def load_fair():
        try:
            load = os.getloadavg()[0] / _cpu_count
        except OSError:  # as of May 2016, Windows' Linux subsystem throws OSError on getloadavg
            load = -1
        return 'load', load
else:  # pragma: no cover
    from dmoj.utils.winperfmon import PerformanceCounter
    from threading import Thread
    from collections import deque
    from time import sleep

    class SystemLoadThread(Thread):
        def __init__(self):
            super(SystemLoadThread, self).__init__()
            self.daemon = True
            self.samples = deque(maxlen=10)
            self.load = 0.5
            self.counter = PerformanceCounter(r'\System\Processor Queue Length', r'\Processor(_Total)\% Processor Time')

        def run(self):
            while True:
                pql, pt = self.counter.query()
                self.samples.append(pql)
                if pt >= 100:
                    self.load = max(sum(self.samples) / len(self.samples) / _cpu_count, pt / 100.)
                else:
                    self.load = pt / 100.
                sleep(1)

    _load_thread = SystemLoadThread()
    _load_thread.start()

    def load_fair():
        return 'load', _load_thread.load


def cpu_count():
    return 'cpu-count', _cpu_count


report_callbacks = [load_fair, cpu_count]
