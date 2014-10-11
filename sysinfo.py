import os
from multiprocessing import cpu_count

_cpu_count = cpu_count()


def load_fair():
    return ('load', os.getloadavg()[0] / _cpu_count)


def cpu_count():
    return ('cpu-count', _cpu_count)


report_callbacks = [load_fair, cpu_count]
