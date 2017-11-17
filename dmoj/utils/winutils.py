import os
import signal
from ctypes import windll, c_size_t, Structure, sizeof, byref, c_uint64
from ctypes.wintypes import DWORD, HANDLE, POINTER, BOOL, WinError

if os.name != 'nt':
    raise ImportError('No module named winutils')

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
    times = [c_uint64() for i in 'a' * 4]
    GetProcessTimes(handle, *map(byref, times))
    return (times[2].value + times[3].value) / 10000000.


SYNCHRONIZE = 0x00100000
WAIT_TIMEOUT = 0x00000102
INFINITE = 0xFFFFFFFF

OpenThread = windll.kernel32.OpenThread
OpenThread.argtypes = (DWORD, BOOL, DWORD)
OpenThread.restype = HANDLE

WaitForMultipleObjects = windll.kernel32.WaitForMultipleObjects
WaitForMultipleObjects.argtypes = (DWORD, POINTER(HANDLE), BOOL, DWORD)
WaitForMultipleObjects.restype = DWORD


def get_handle_of_thread(thread, access):
    return OpenThread(access, False, thread.ident)


def wait_for_multiple_objects(handles, timeout=INFINITE, all=False):
    array = (HANDLE * len(handles))(*handles)
    res = WaitForMultipleObjects(len(handles), array, all, timeout)
    if res == INFINITE:
        raise WinError()
    elif res == WAIT_TIMEOUT:
        return None
    return res

_signal_map = {
    signal.SIGABRT: 'Aborted',
    signal.SIGINT: 'Interrupted',
    signal.SIGTERM: 'Terminated',
    signal.SIGFPE: 'Floating point exception',
    signal.SIGILL: 'Illegal instruction',
    signal.SIGSEGV: 'Segmentation fault',
}


def strsignal(signum):
    return _signal_map.get(signum) or 'signal %d' % signum
