import os
from multiprocessing import cpu_count

cpu_count = cpu_count()


def load_fair():
    return os.getloadavg()[0] / cpu_count
