import re
import sys
from .sandbox import ALLOW
from .syscalls import *


class CHROOTSecurity(dict):
    def __init__(self, filesystem, writable=(1, 2)):
        super(CHROOTSecurity, self).__init__()
        self.fs_jail = re.compile('|'.join(filesystem) if filesystem else '^')
        self.execve_count = 0
        self._writable = writable

        self.update({
            sys_execve: self.do_execve,
            sys_read: ALLOW,
            sys_write: self.do_write,
            sys_writev: self.do_write,
            sys_open: self.do_access,
            sys_access: self.do_access,
            sys_close: ALLOW,
            sys_stat: ALLOW,
            sys_dup: ALLOW,
            sys_fstat: ALLOW,
            sys_mmap: ALLOW,
            sys_mremap: ALLOW,
            sys_mprotect: ALLOW,
            sys_munmap: ALLOW,
            sys_brk: ALLOW,
            sys_fcntl: ALLOW,
            sys_arch_prctl: ALLOW,
            sys_set_tid_address: ALLOW,
            sys_set_robust_list: ALLOW,
            sys_futex: ALLOW,
            sys_rt_sigaction: ALLOW,
            sys_rt_sigprocmask: ALLOW,
            sys_getrlimit: ALLOW,
            sys_ioctl: ALLOW,
            sys_readlink: ALLOW,
            sys_getcwd: ALLOW,
            sys_geteuid: ALLOW,
            sys_getuid: ALLOW,
            sys_getegid: ALLOW,
            sys_getgid: ALLOW,
            sys_lstat: ALLOW,
            sys_openat: ALLOW,
            sys_getdents: ALLOW,
            sys_lseek: ALLOW,
            sys_getrusage: ALLOW,
            sys_sigaltstack: ALLOW,
            sys_pipe: ALLOW,
            sys_clock_gettime: ALLOW,
            sys_gettimeofday: ALLOW,

            sys_clone: ALLOW,
            sys_exit_group: ALLOW,
            sys_gettid: ALLOW,

            # x86 specific
            sys_mmap2: ALLOW,
            sys_fstat64: ALLOW,
            sys_set_thread_area: ALLOW,
            sys_ugetrlimit: ALLOW,
            sys_uname: ALLOW,
            sys_getuid32: ALLOW,
            sys_geteuid32: ALLOW,
            sys_getgid32: ALLOW,
            sys_getegid32: ALLOW,
            sys_stat64: ALLOW,
            sys_lstat64: ALLOW,
            sys_llseek: ALLOW,
            sys_fcntl64: ALLOW,
            sys_time: ALLOW,
            sys_prlimit64: ALLOW,
            sys_getdents64: ALLOW,
        })

    def do_write(self, debugger):
        return debugger.arg0() in self._writable

    def do_execve(self, debugger):
        self.execve_count += 1
        return self.execve_count < 2

    def do_access(self, debugger):
        file = debugger.readstr(debugger.uarg0())
        if self.fs_jail.match(file) is None:
            print>>sys.stderr, 'Not allowed to access:', file
            return False
        return True
