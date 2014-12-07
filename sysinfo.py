import os
from multiprocessing import cpu_count

_cpu_count = cpu_count()


if hasattr(os, 'getloadavg'):
    def load_fair():
        return 'load', os.getloadavg()[0] / _cpu_count
else:
    def load_fair():
        return 'load', 0.5


def cpu_count():
    return 'cpu-count', _cpu_count


report_callbacks = [load_fair, cpu_count]
