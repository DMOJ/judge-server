from functools import wraps
import os
from signal import *
import time
from _ptrace import *

__all__ = ['ProcessDebugger', 'syscall', 'unsafe_syscall']


class ProcessDebugger(object):
    def __init__(self):
        def undefined_method():
            raise NotImplementedError("you can only access arguments once a process has been attached")

        @property
        def undefined_property():
            raise NotImplementedError("you can only access process members once a process has been attached")

        self.arg0 = undefined_method
        self.arg1 = undefined_method
        self.arg2 = undefined_method
        self.arg3 = undefined_method
        self.arg4 = undefined_method
        self.arg5 = undefined_method
        self.get_syscall_number = undefined_method
        self.pid = undefined_property


def syscall(func):
    @wraps(func)
    def delegate(self, *args, **kwargs):
        pid = self.pid
        if func(self, *args, **kwargs):
            ptrace(PTRACE_SYSCALL, pid, None, None)
            self._tt += time.time() - self._st
            return True
        return False

    return delegate


def unsafe_syscall(func):
    """
        ptrace recieves notifications prior to the kernel reading the memory pointed to by the registers.
        It is theoretically possible to modify a pointer after ptbox finishes validation but
        before the memory is actually accessed, given a multiprocess task.

        Hence, here we stop all child tasks (SIGSTOP), execute the syscall, then resume all tasks (SIGCONT).
    """

    @wraps(func)
    def halter(self, *args, **kwargs):
        pid = self.pid
        tasks = map(int, os.listdir("/proc/%d/task" % pid))
        tasks.remove(pid)
        if tasks:
            for task in tasks:
                os.kill(task, SIGSTOP)
        ret = func(self, *args, **kwargs)
        if ret:
            ptrace(PTRACE_SYSCALL, pid, None, None)
        t = time.time()
        if tasks:
            for task in tasks:
                os.kill(task, SIGCONT)
        self._tt += time.time() - self._st
        return ret

    return halter