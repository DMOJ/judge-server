import os
from multiprocessing import cpu_count
from threading import Thread
from collections import deque
import subprocess

_cpu_count = cpu_count()


if hasattr(os, 'getloadavg'):
    def load_fair():
        return 'load', os.getloadavg()[0] / _cpu_count
else:
    class SystemLoadThread(Thread):
        def __init__(self):
            super(SystemLoadThread, self).__init__(None, None, None, (), None, None)
            self.daemon = True
            self.process = None
            self.terminate = False
            self.samples = deque(maxlen=60)
            self.load = 0.5

        def run(self):
            self.process = subprocess.Popen(['typeperf', 'System\Processor Queue Length'], stdout=subprocess.PIPE)
            read = self.process.stdout
            while not read.readline().strip():
                pass

            while True:
                line = read.readline()
                if self.terminate or '","' not in line:
                    break
                self.samples.append(float(line.strip().split('","')[1][:-1]))
                self.load = sum(self.samples) / len(self.samples)

    load_thread = SystemLoadThread()
    load_thread.start()

    def load_fair():
        return 'load', load_thread.load / _cpu_count


def cpu_count():
    return 'cpu-count', _cpu_count


report_callbacks = [load_fair, cpu_count]
