import logging
import os
import re
import sys

from dmoj.cptbox._cptbox import AT_FDCWD, bsd_get_proc_cwd, bsd_get_proc_fdno
from dmoj.cptbox.handlers import ACCESS_EACCES, ACCESS_ENOENT, ACCESS_EPERM, ALLOW
# noinspection PyUnresolvedReferences
from dmoj.cptbox.syscalls import *
from dmoj.utils.unicode import utf8text

log = logging.getLogger('dmoj.security')


class IsolateTracer(dict):
    def __init__(self, read_fs, write_fs=None, writable=(1, 2)):
        super().__init__()
        self.read_fs = read_fs
        self.write_fs = write_fs
        self.read_fs_jail = {}
        self.write_fs_jail = {}

        self._writable = list(writable)

        if sys.platform.startswith('freebsd'):
            self._getcwd_pid = lambda pid: utf8text(bsd_get_proc_cwd(pid))
            self._getfd_pid = lambda pid, fd: utf8text(bsd_get_proc_fdno(pid, fd))
        else:
            self._getcwd_pid = lambda pid: os.readlink('/proc/%d/cwd' % pid)
            self._getfd_pid = lambda pid, fd: os.readlink('/proc/%d/fd/%d' % (pid, fd))

        self.update({
            # Deny with report
            sys_openat: self.check_file_access_at('openat', is_open=True),
            sys_open: self.check_file_access('open', 0, is_open=True),
            sys_faccessat: self.check_file_access_at('faccessat'),
            sys_access: self.check_file_access('access', 0),
            sys_readlink: self.check_file_access('readlink', 0),
            sys_readlinkat: self.check_file_access_at('readlinkat'),
            sys_stat: self.check_file_access('stat', 0),
            sys_stat64: self.check_file_access('stat64', 0),
            sys_lstat: self.check_file_access('lstat', 0),
            sys_lstat64: self.check_file_access('lstat64', 0),
            sys_fstatat: self.check_file_access_at('fstatat'),
            sys_mkdir: ACCESS_EPERM,
            sys_unlink: ACCESS_EPERM,
            sys_tgkill: self.do_kill,
            sys_kill: self.do_kill,
            sys_prctl: self.do_prctl,

            sys_read: ALLOW,
            sys_write: ALLOW,
            sys_writev: ALLOW,
            sys_statfs: ALLOW,
            sys_statfs64: ALLOW,
            sys_getpgrp: ALLOW,
            sys_restart_syscall: ALLOW,
            sys_select: ALLOW,
            sys_newselect: ALLOW,
            sys_modify_ldt: ALLOW,
            sys_ppoll: ALLOW,

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

            sys_socket: ACCESS_EACCES,
            sys_socketcall: ACCESS_EACCES,

            sys_close: ALLOW,
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
            sys_getcwd: ALLOW,
            sys_geteuid: ALLOW,
            sys_getuid: ALLOW,
            sys_getegid: ALLOW,
            sys_getgid: ALLOW,
            sys_getdents: ALLOW,
            sys_lseek: ALLOW,
            sys_getrusage: ALLOW,
            sys_sigaltstack: ALLOW,
            sys_pipe: ALLOW,
            sys_pipe2: ALLOW,
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
            sys_llseek: ALLOW,
            sys_fcntl64: ALLOW,
            sys_time: ALLOW,
            sys_prlimit64: self.do_prlimit,
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
                sys_shm_open: self.check_file_access('shm_open', 0),
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
                sys_cap_getmode: ALLOW,
                sys_minherit: ALLOW,
            })

    def is_write_flags(self, open_flags):
        O_TMPFILE = 0x410000  # os.O_TMPFILE not defined in Python 2
        for flag in [os.O_WRONLY, os.O_RDWR, os.O_TRUNC, os.O_CREAT, os.O_EXCL, O_TMPFILE]:
            # Strict equality is necessary here, since e.g. O_TMPFILE has multiple bits set,
            # and O_DIRECTORY & O_TMPFILE > 0.
            if open_flags & flag == flag:
                return True

        return False

    def check_file_access(self, syscall, argument, is_open=False):
        def check(debugger):
            file_ptr = getattr(debugger, 'uarg%d' % argument)
            file = debugger.readstr(file_ptr)
            file, accessible = self._file_access_check(file, debugger, is_open)
            if accessible:
                return True

            log.info('Denied access via syscall %s: %s', syscall, file)
            return ACCESS_ENOENT(debugger)
        return check

    def check_file_access_at(self, syscall, is_open=False):
        def check(debugger):
            file = debugger.readstr(debugger.uarg1)
            file, accessible = self._file_access_check(file, debugger, is_open, dirfd=debugger.arg0, flag_reg=2)
            if accessible:
                return True

            log.info('Denied access via syscall %s: %s', syscall, file)
            return ACCESS_ENOENT(debugger)
        return check

    def _get_fs_jail(self, debugger, is_write):
        # The only syscalls that can ever have is_write=True are open and
        # openat: if we ever want to support syscalls like unlink or mkdir,
        # this behaviour will need to be changed. Currently, they result in
        # an unconditional EPERM.
        jail = self.write_fs_jail if is_write else self.read_fs_jail
        fs = jail.get(debugger.pid)

        if fs is None:
            fs_parts = self.write_fs if is_write else self.read_fs
            if fs_parts:
                fs_re = '|'.join(map(lambda p: p.format(pid=debugger.pid), fs_parts))
            else:
                fs_re = '(?!)'  # Disallow accessing everything by default.

            fs = re.compile(fs_re)
            jail[debugger.pid] = fs

        return fs

    def _file_access_check(self, rel_file, debugger, is_open, flag_reg=1, dirfd=AT_FDCWD):
        try:
            file = self.get_full_path(debugger, rel_file, dirfd)
        except UnicodeDecodeError:
            log.exception('Unicode decoding error while opening relative to %d: %r', dirfd, rel_file)
            return '(undecodable)', False

        is_write = is_open and self.is_write_flags(getattr(debugger, 'uarg%d' % flag_reg))
        if self._get_fs_jail(debugger, is_write).match(file) is None:
            return file, False
        return file, True

    def get_full_path(self, debugger, file, dirfd=AT_FDCWD):
        dirfd = (dirfd & 0x7FFFFFFF) - (dirfd & 0x80000000)
        if not file.startswith('/'):
            dir = (self._getcwd_pid(debugger.pid) if dirfd == AT_FDCWD else
                   self._getfd_pid(debugger.pid, dirfd))
            file = os.path.join(dir, file)
        file = '/' + os.path.normpath(file).lstrip('/')
        return file

    def do_kill(self, debugger):
        # Allow tgkill to execute as long as the target thread group is the debugged process
        # libstdc++ seems to use this to signal itself, see <https://github.com/DMOJ/judge/issues/183>
        return True if debugger.uarg0 == debugger.pid else ACCESS_EPERM(debugger)

    def do_prlimit(self, debugger):
        return True if debugger.uarg0 in (0, debugger.pid) else ACCESS_EPERM(debugger)

    def do_prctl(self, debugger):
        PR_GET_DUMPABLE = 3
        PR_SET_NAME = 15
        PR_GET_NAME = 16
        PR_SET_VMA = 0x53564d41  # Used on Android
        return debugger.arg0 in (PR_GET_DUMPABLE, PR_SET_NAME, PR_GET_NAME, PR_SET_VMA)
