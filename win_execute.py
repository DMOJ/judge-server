import sys
import subprocess
import time

from ctypes.wintypes import *
from ctypes import *

GetCurrentProcess = windll.kernel32.GetCurrentProcess  # @UndefinedVariable
GetCurrentProcess.argtypes = []
GetCurrentProcess.restype = HANDLE

OpenProcess = windll.kernel32.OpenProcess  # @UndefinedVariable
OpenProcess.restype = HANDLE

PROCESS_ALL_ACCESS = 2035711

class win_Process(object):
    def __init__(self, chained):
        self._chained = chained
        self.stdout = chained.stdout
        self.stdin = chained.stdin
        self.usages = None
        self.returncode = None

        self._start_time = time.time()

    def __getattr__(self, name):
        if name in ["wait", "send_signal", "terminate", "kill", "poll"]:
            return getattr(self._chained, name)
        return object.__getattribute__(self, name)

    def get_execution_time(self):
        return time.time() - self._start_time

    def get_max_memory(self):
        return get_memory_info(OpenProcess(PROCESS_ALL_ACCESS, True, self._chained.pid))["PeakPagefileUsage"]/1024.0

def execute(path):
    process = subprocess.Popen(path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return win_Process(process)

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

if __name__ == "__main__":
    pass
