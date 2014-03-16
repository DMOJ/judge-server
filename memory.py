__all__ = ['get_current_process', 'get_memory_info', 'get_memory_usage']

from ctypes.wintypes import *
from ctypes import *

GetCurrentProcess = windll.kernel32.GetCurrentProcess  # @UndefinedVariable
GetCurrentProcess.argtypes = []
GetCurrentProcess.restype = HANDLE

OpenProcess = windll.kernel32.OpenProcess  # @UndefinedVariable
OpenProcess.restype = HANDLE

PROCESS_ALL_ACCESS = 2035711

class PROCESS_MEMORY_COUNTERS_EX(Structure):
    _fields_ = [
        ('cb', DWORD),
        ('PageFaultCount', DWORD),
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


GetProcessMemoryInfo = windll.psapi.GetProcessMemoryInfo
GetProcessMemoryInfo.argtypes = [
    HANDLE,
    POINTER(PROCESS_MEMORY_COUNTERS_EX),
    DWORD,
]
GetProcessMemoryInfo.restype = BOOL


def get_current_process():
    """Return handle to current process."""
    return GetCurrentProcess()


def get_memory_info(process=None):
    """Return Win32 process memory counters structure as a dict."""
    if process is None:
        process = get_current_process()
    counters = PROCESS_MEMORY_COUNTERS_EX()
    ret = GetProcessMemoryInfo(process, byref(counters), sizeof(counters))
    if not ret:
        raise WinError()
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
