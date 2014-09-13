import re
from .sandbox import ALLOW
from .syscalls import *


class CHROOTSecurity(dict):
    def __init__(self, filesystem):
        super(CHROOTSecurity, self).__init__()
        self.fs_jail = re.compile('|'.join(filesystem) if filesystem else '^')
        self.execve_count = 0

        self.update({
            sys_execve: self.do_execve,
            sys_read: ALLOW,
            sys_write: self.do_write,
            sys_open: self.do_access,
            sys_access: self.do_access,
            sys_close: ALLOW,
            sys_stat: ALLOW,
            sys_dup: ALLOW,
            sys_fstat: ALLOW,
            sys_mmap: ALLOW,
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

            sys_clone: ALLOW,
            sys_exit_group: ALLOW,
        })

    @staticmethod
    def do_write(debugger):
        return debugger.arg0() in (1, 2)

    def do_execve(self, debugger):
        self.execve_count += 1
        return self.execve_count < 2

    def do_access(self, debugger):
        file = debugger.readstr(debugger.uarg0())
        return self.fs_jail.match(file) is not None
