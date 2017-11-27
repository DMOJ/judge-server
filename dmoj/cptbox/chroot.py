from __future__ import print_function

import re
import sys
import os
import logging

from dmoj.cptbox.handlers import ALLOW, STDOUTERR, ACCESS_DENIED
from dmoj.cptbox._cptbox import bsd_get_proc_cwd, bsd_get_proc_fdno, AT_FDCWD
from dmoj.cptbox.syscalls import *


log = logging.getLogger('dmoj.security')


class CHROOTSecurity(dict):
    def __init__(self, filesystem, writable=(1, 2), io_redirects=None):
        super(CHROOTSecurity, self).__init__()
        self.fs_jail = re.compile('|'.join(filesystem) if filesystem else '^')
        self._writable = list(writable)
        self._io_redirects = io_redirects

        if sys.platform.startswith('freebsd'):
            self._getcwd_pid = bsd_get_proc_cwd
            self._getfd_pid = bsd_get_proc_fdno
        else:
            self._getcwd_pid = lambda pid: os.readlink('/proc/%d/cwd' % pid)
            self._getfd_pid = lambda pid, fd: os.readlink('/proc/%d/fd/%d' % (pid, fd))

        self.update({
            sys_read: ALLOW,
            sys_write: ALLOW,
            sys_writev: ALLOW,
            sys_open: self.do_open,
            sys_openat: self.do_openat,
            sys_access: self.do_access,
            sys_faccessat: self.do_faccessat,
            # Deny with report
            sys_mkdir: self.deny_with_file_path('mkdir', 0),
            sys_unlink: self.deny_with_file_path('unlink', 0),
            sys_tgkill: self.do_tgkill,
            sys_kill: self.do_kill,
            sys_prctl: self.do_prctl,

            sys_statfs: ALLOW,
            sys_statfs64: ALLOW,
            sys_getpgrp: ALLOW,
            sys_restart_syscall: ALLOW,
            sys_select: ALLOW,
            sys_newselect: ALLOW,
            sys_modify_ldt: ALLOW,

            sys_getgroups32: ALLOW,
            sys_sched_getaffinity: ALLOW,
            sys_sched_getparam: ALLOW,
            sys_sched_getscheduler: ALLOW,
            sys_sched_get_priority_min: ALLOW,
            sys_sched_get_priority_max: ALLOW,
            sys_timerfd_create: ALLOW,
            sys_timer_create: ALLOW,
            sys_timer_settime: ALLOW,
            sys_timer_delete: ALLOW,

            sys_sigprocmask: ALLOW,
            sys_rt_sigreturn: ALLOW,
            sys_sigreturn: ALLOW,
            sys_nanosleep: ALLOW,
            sys_sysinfo: ALLOW,
            sys_getrandom: ALLOW,

            sys_socket: ACCESS_DENIED,
            sys_socketcall: ACCESS_DENIED,

            sys_close: ALLOW,
            sys_stat: ALLOW,
            sys_dup: ALLOW,
            sys_dup2: ALLOW,
            sys_dup3: ALLOW,
            sys_fstat: ALLOW,
            sys_mmap: ALLOW,
            sys_mremap: ALLOW,
            sys_mprotect: ALLOW,
            sys_madvise: ALLOW,
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
            sys_getdents: ALLOW,
            sys_lseek: ALLOW,
            sys_getrusage: ALLOW,
            sys_sigaltstack: ALLOW,
            sys_pipe: ALLOW,
            sys_clock_gettime: ALLOW,
            sys_clock_getres: ALLOW,
            sys_gettimeofday: ALLOW,
            sys_getpid: ALLOW,
            sys_getppid: ALLOW,
            sys_sched_yield: ALLOW,

            sys_clone: ALLOW,
            sys_exit: ALLOW,
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

        # FreeBSD-specific syscalls
        if 'freebsd' in sys.platform:
            self.update({
                sys_obreak: ALLOW,
                sys_sysarch: ALLOW,
                sys_sysctl: ALLOW,  # TODO: More strict?
                sys_issetugid: ALLOW,
                sys_rtprio_thread: ALLOW,  # EPERMs when invalid anyway
                sys_umtx_op: ALLOW,  # http://fxr.watson.org/fxr/source/kern/kern_umtx.c?v=FREEBSD60#L720
                sys_nosys: ALLOW,  # what?? TODO: this shouldn't really exist, so why is Python calling it?
                sys_getcontext: ALLOW,
                sys_setcontext: ALLOW,
                sys_pread: ALLOW,
                sys_fsync: ALLOW,
                sys_shm_open: self.do_open,
                sys_cpuset_getaffinity: ALLOW,
                sys_thr_new: ALLOW,
                sys_thr_exit: ALLOW,
                sys_thr_kill: ALLOW,
                sys_thr_self: ALLOW,
                sys__mmap: ALLOW,
                sys___mmap: ALLOW,
                sys_sigsuspend: ALLOW,
                sys_clock_getcpuclockid2: ALLOW,
                sys_fstatfs: ALLOW,
                sys_getdirentries: ALLOW,  # TODO: maybe check path?
                sys_getdtablesize: ALLOW,
                sys_kqueue: ALLOW,
                sys_kevent: ALLOW,
                sys_ktimer_create: ALLOW,
                sys_ktimer_settime: ALLOW,
                sys_ktimer_delete: ALLOW,
            })

    def deny_with_file_path(self, syscall, argument):
        def check(debugger):
            file = debugger.readstr(getattr(debugger, 'uarg%d' % argument))
            print('%s: not allowed to access: %s' % (syscall, file), file=sys.stderr)
            log.warning('Denied access via syscall %s: %s', syscall, file)
            return False

        return check

    def do_access(self, debugger):
        file = debugger.readstr(debugger.uarg0)
        return self._file_access_check(file, debugger) or ACCESS_DENIED(debugger)

    def do_open(self, debugger):
        file_ptr = debugger.uarg0
        file = debugger.readstr(file_ptr)
        return self._file_access_check(file, debugger, file_ptr)

    def _handle_io_redirects(self, file, debugger, file_ptr):
        data = self._io_redirects.get(file, None)

        if data:
            user_mode, redirect = data
            kernel_flags = debugger.uarg1

            # File is open for read if it is not open for write, unless it's open for both read/write
            is_valid_read = 'r' in user_mode and (not (kernel_flags & os.O_WRONLY) or kernel_flags & os.O_RDWR)
            is_valid_write = 'w' in user_mode and (kernel_flags & os.O_WRONLY or kernel_flags & os.O_RDWR) \
                             and redirect in self._writable

            if is_valid_read or is_valid_write:
                # We have to duplicate the handle so that in case a program decides to close it,
                # the original will not be closed as well.
                # To do this, we can hijack the current open call and replace it with a dup call.
                # The structure of a dup call is syscall=sys_dup, arg0=id to dup, so let's set that up.
                debugger.syscall = debugger.get_syscall_id(sys_dup)
                debugger.uarg0 = redirect

                # Once the syscall executes, the result will be our dup'd handle.
                def on_return():
                    handle = debugger.result
                    self._writable.append(handle)

                    # dup overrides the ebx register with the redirect fd, but we should return it back to the
                    # file pointer in case some program requires it to remain in the register post-syscall.
                    # The final two args for sys_open (flags & mode) are untouched by sys_dup, so we can leave
                    # them as-is.
                    debugger.uarg0 = file_ptr

                debugger.on_return(on_return)

                return True

    def _file_access_check(self, rel_file, debugger, file_ptr=None, dirfd=AT_FDCWD):
        file = self.get_full_path(debugger, rel_file, dirfd)
        if file_ptr and self._io_redirects:
            for path in (rel_file, os.path.basename(file), file):
                if self._handle_io_redirects(path, debugger, file_ptr):
                    return True
        if self.fs_jail.match(file) is None:
            log.warning('Denied file open: %s', file)
            return False
        return True

    def get_full_path(self, debugger, file, dirfd=AT_FDCWD):
        dirfd = (dirfd & 0x7FFFFFFF) - (dirfd & 0x80000000)
        if not file.startswith('/'):
            dir = (self._getcwd_pid(debugger.pid) if dirfd == AT_FDCWD else
                   self._getfd_pid(debugger.pid, dirfd))
            file = os.path.join(dir, file)
        file = '/' + os.path.normpath(file).lstrip('/')
        return file

    def do_openat(self, debugger):
        file_ptr = debugger.uarg1
        file = debugger.readstr(file_ptr)
        return self._file_access_check(file, debugger, file_ptr, dirfd=debugger.arg0)

    def do_faccessat(self, debugger):
        file = debugger.readstr(debugger.uarg1)
        return self._file_access_check(file, debugger, dirfd=debugger.arg0)

    def do_kill(self, debugger):
        return debugger.uarg0 == debugger.pid

    def do_tgkill(self, debugger):
        tgid = debugger.uarg0

        # Allow tgkill to execute as long as the target thread group is the debugged process
        # libstdc++ seems to use this to signal itself, see <https://github.com/DMOJ/judge/issues/183>
        return tgid == debugger.pid

    def do_prctl(self, debugger):
        # PR_SET_NAME = 15
        return debugger.arg0 in (15,)
