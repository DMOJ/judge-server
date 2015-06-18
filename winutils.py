import os
if os.name != 'nt':
    raise ImportError('No module named winutils')

from ctypes import windll, c_size_t, Structure, sizeof, byref, c_uint64
from ctypes.wintypes import DWORD, HANDLE, POINTER

__all__ = ['max_memory', 'execution_time']


class PROCESS_MEMORY_COUNTERS(Structure):
    _fields_ = [("cb", DWORD),
                ("PageFaultCount", DWORD),
                ("PeakWorkingSetSize", c_size_t),
                ("WorkingSetSize", c_size_t),
                ("QuotaPeakPagedPoolUsage", c_size_t),
                ("QuotaPagedPoolUsage", c_size_t),
                ("QuotaPeakNonPagedPoolUsage", c_size_t),
                ("QuotaNonPagedPoolUsage", c_size_t),
                ("PagefileUsage", c_size_t),
                ("PeakPagefileUsage", c_size_t)]

    def __init__(self):
        self.cb = sizeof(self)


GetProcessMemoryInfo = windll.psapi.GetProcessMemoryInfo
GetProcessMemoryInfo.argtypes = (HANDLE, POINTER(PROCESS_MEMORY_COUNTERS), DWORD)
GetProcessTimes = windll.kernel32.GetProcessTimes


def max_memory(handle):
    pmi = PROCESS_MEMORY_COUNTERS()
    if not GetProcessMemoryInfo(handle, byref(pmi), sizeof(pmi)):
        raise WindowsError()
    return pmi.PeakWorkingSetSize


def execution_time(handle):
    times = [c_uint64() for i in xrange(4)]
    GetProcessTimes(handle, *map(byref, times))
    return (times[2].value + times[3].value) / 10000000.