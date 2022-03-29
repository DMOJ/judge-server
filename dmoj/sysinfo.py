import os
from multiprocessing import cpu_count as _get_cpu_count

_cpu_count = _get_cpu_count()


if hasattr(os, 'getloadavg'):

    def load_fair():
        try:
            load = os.getloadavg()[0] / _cpu_count
        except OSError:  # as of May 2016, Windows' Linux subsystem throws OSError on getloadavg
            load = -1
        return 'load', load

else:
    # There exist some Unix platforms (like Android) which don't
    # have `getloadavg` implemented, but aren't Windows
    # so we manually read the `/proc/loadavg` file.
    def load_fair():
        try:
            with open('/proc/loadavg', 'r') as f:
                load = float(f.read().split()[0]) / _cpu_count
        except FileNotFoundError:
            load = -1
        return 'load', load


def cpu_count():
    return 'cpu-count', _cpu_count


report_callbacks = [load_fair, cpu_count]
