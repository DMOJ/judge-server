__all__ = ['get_current_process', 'get_memory_info', 'get_memory_usage']

import ctypes
from ctypes import wintypes
from ctypes import *

GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess  # @UndefinedVariable
GetCurrentProcess.argtypes = []
GetCurrentProcess.restype = wintypes.HANDLE

OpenProcess = ctypes.windll.kernel32.OpenProcess  # @UndefinedVariable
OpenProcess.restype = wintypes.HANDLE

PROCESS_ALL_ACCESS = 2035711

class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', c_size_t),
        ('WorkingSetSize', c_size_t),
        ('QuotaPeakPagedPoolUsage', c_size_t),
        ('QuotaPagedPoolUsage', c_size_t),
        ('QuotaPeakNonPagedPoolUsage', c_size_t),
        ('QuotaNonPagedPoolUsage', c_size_t),
        ('PagefileUsage', c_size_t),
        ('PeakPagefileUsage', c_size_t),
        ('PrivateUsage', c_size_t),
    ]


GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
    wintypes.DWORD,
]
GetProcessMemoryInfo.restype = wintypes.BOOL


def get_current_process():
    """Return handle to current process."""
    return GetCurrentProcess()


def get_memory_info(process=None):
    """Return Win32 process memory counters structure as a dict."""
    if process is None:
        process = get_current_process()
    counters = PROCESS_MEMORY_COUNTERS_EX()
    ret = GetProcessMemoryInfo(process, ctypes.byref(counters),
                               ctypes.sizeof(counters))
    if not ret:
        raise ctypes.WinError()
    info = dict((name, getattr(counters, name))
                for name, _ in counters._fields_)
    return info


def get_memory_usage(process=None):
    """Return this process's memory usage in bytes."""
    info = get_memory_info(process=process)
    return info['PrivateUsage']


if __name__ == '__main__':
    import pprint

    pprint.pprint(get_memory_info())
