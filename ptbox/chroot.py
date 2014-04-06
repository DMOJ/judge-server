import os
import re
from __init__ import *
from syscalls import *


class CHROOTProcessDebugger(ProcessDebugger):
    def __init__(self, filesystem=None):
        super(CHROOTProcessDebugger, self).__init__()
        self.fs_jail = re.compile('|'.join(filesystem) if filesystem else ".*")
        self.execve_count = 0
        self.__proc_mem = None

    def __del__(self):
        os.close(self.__proc_mem)

    def get_handlers(self):
        do_allow = self.do_allow
        return {
            sys_execve: self.do_execve,
            sys_read: do_allow,
            sys_write: self.do_write,
            sys_open: self.do_open,
            sys_access: self.do_access,
            sys_close: do_allow,
            sys_stat: do_allow,
            sys_fstat: do_allow,
            sys_mmap: do_allow,
            sys_mprotect: do_allow,
            sys_munmap: do_allow,
            sys_brk: do_allow,
            sys_fcntl: do_allow,
            sys_arch_prctl: do_allow,
            sys_set_tid_address: do_allow,
            sys_set_robust_list: do_allow,
            sys_futex: do_allow,
            sys_rt_sigaction: do_allow,
            sys_rt_sigprocmask: do_allow,
            sys_getrlimit: do_allow,
            sys_ioctl: do_allow,
            sys_readlink: do_allow,
            sys_getcwd: do_allow,
            sys_geteuid: do_allow,
            sys_getuid: do_allow,
            sys_getegid: do_allow,
            sys_getgid: do_allow,
            sys_lstat: do_allow,
            sys_openat: do_allow,
            sys_getdents: do_allow,
            sys_lseek: do_allow,
            sys_getrusage: do_allow,
            sys_sigaltstack: do_allow,
            sys_pipe: do_allow,
            sys_clock_gettime: do_allow,

            sys_clone: do_allow,
            sys_exit_group: do_allow,
        }

    @syscall
    def do_allow(self):
        return True

    @syscall
    def do_write(self):
        fd = self.arg0().as_int
        # Only allow writing to stdout & stderr
        return fd == 1 or fd == 2

    @unsafe_syscall
    def do_execve(self):
        self.execve_count += 1
        if self.execve_count > 2:
            return False
        return True

    def __do_access(self):
        try:
            addr = self.arg0().as_uint64
            if addr > 0:
                #proc_mem = open("/proc/%d/mem" % pid, "rb")
                #proc_mem.seek(addr, 0)
                if self.__proc_mem is None:
                    self.__proc_mem = os.open('/proc/%d/mem' % self.pid, os.O_RDONLY)
                os.lseek(self.__proc_mem, addr, os.SEEK_SET)
                buf = ''
                page = (addr + 4096) // 4096 * 4096 - addr
                while True:
                    #buf += proc_mem.read(page)
                    buf += os.read(self.__proc_mem, page)
                    if '\0' in buf:
                        buf = buf[:buf.index('\0')]
                        break
                    page = 4096
        except:
            return True
        #print buf
        return self.fs_jail.match(buf)
        return True

    @unsafe_syscall
    def do_access(self):
        return self.__do_access()

    @unsafe_syscall
    def do_open(self):
        flags = self.arg1().as_int
        # TODO: kill if write
        return self.__do_access()