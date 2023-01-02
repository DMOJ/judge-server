import logging
import os
import sys
from enum import Enum
from typing import Any, Callable, Mapping, Sequence

from dmoj.cptbox._cptbox import AT_FDCWD, Debugger, bsd_get_proc_cwd, bsd_get_proc_fdno
from dmoj.cptbox.filesystem_policies import FilesystemAccessRule, FilesystemPolicy
from dmoj.cptbox.handlers import (
    ACCESS_EACCES,
    ACCESS_EFAULT,
    ACCESS_ENAMETOOLONG,
    ACCESS_ENOENT,
    ACCESS_EPERM,
    ALLOW,
    ErrnoHandlerCallback,
)
from dmoj.cptbox.syscalls import *
from dmoj.cptbox.syscalls import by_id
from dmoj.cptbox.tracer import HandlerCallback, MaxLengthExceeded
from dmoj.utils.unicode import utf8text

log = logging.getLogger('dmoj.security')
open_write_flags = [os.O_WRONLY, os.O_RDWR, os.O_TRUNC, os.O_CREAT, os.O_EXCL]

try:
    open_write_flags.append(os.O_TMPFILE)
except AttributeError:
    # This may not exist on FreeBSD, so we ignore.
    pass


class FilesystemSyscallKind(Enum):
    READ = 1
    WRITE = 2


AccessChecker = Callable[[Debugger], None]

FSJailGetter = Callable[[Debugger], FilesystemPolicy]
DirFDGetter = Callable[[Debugger], int]


class IsolateTracer(dict):
    def __init__(self, *, read_fs: Sequence[FilesystemAccessRule], write_fs: Sequence[FilesystemAccessRule]):
        super().__init__()
        self.read_fs_jail = self._compile_fs_jail(read_fs)
        self.write_fs_jail = self._compile_fs_jail(write_fs)

        if sys.platform.startswith('freebsd'):
            self._getcwd_pid = lambda pid: utf8text(bsd_get_proc_cwd(pid))
            self._getfd_pid = lambda pid, fd: utf8text(bsd_get_proc_fdno(pid, fd))
        else:
            self._getcwd_pid = lambda pid: os.readlink('/proc/%d/cwd' % pid)
            self._getfd_pid = lambda pid, fd: os.readlink('/proc/%d/fd/%d' % (pid, fd))

        self.update(
            {
                # Deny with report
                sys_openat: self.handle_openat(dir_reg=0, file_reg=1, flag_reg=2),
                sys_open: self.handle_open(file_reg=0, flag_reg=1),
                sys_faccessat: self.handle_file_access_at(FilesystemSyscallKind.READ, dir_reg=0, file_reg=1),
                sys_faccessat2: self.handle_file_access_at(FilesystemSyscallKind.READ, dir_reg=0, file_reg=1),
                sys_access: self.handle_file_access(FilesystemSyscallKind.READ, file_reg=0),
                sys_readlink: self.handle_file_access(FilesystemSyscallKind.READ, file_reg=0),
                sys_readlinkat: self.handle_file_access_at(FilesystemSyscallKind.READ, dir_reg=0, file_reg=1),
                sys_stat: self.handle_file_access(FilesystemSyscallKind.READ, file_reg=0),
                sys_stat64: self.handle_file_access(FilesystemSyscallKind.READ, file_reg=0),
                sys_lstat: self.handle_file_access(FilesystemSyscallKind.READ, file_reg=0),
                sys_lstat64: self.handle_file_access(FilesystemSyscallKind.READ, file_reg=0),
                sys_fstatat: self.handle_fstat(dir_reg=0, file_reg=1),
                sys_statx: self.handle_fstat(dir_reg=0, file_reg=1),
                sys_tkill: self.handle_kill,
                sys_tgkill: self.handle_kill,
                sys_kill: self.handle_kill,
                sys_prctl: self.handle_prctl,
                sys_read: ALLOW,
                sys_pread64: ALLOW,
                sys_write: ALLOW,
                sys_writev: ALLOW,
                sys_statfs: ALLOW,
                sys_statfs64: ALLOW,
                sys_getpgrp: ALLOW,
                sys_restart_syscall: ALLOW,
                sys_select: ALLOW,
                sys_newselect: ALLOW,
                sys_modify_ldt: ALLOW,
                sys_epoll_create: ALLOW,
                sys_epoll_create1: ALLOW,
                sys_epoll_ctl: ALLOW,
                sys_epoll_wait: ALLOW,
                sys_epoll_pwait: ALLOW,
                sys_poll: ALLOW,
                sys_ppoll: ALLOW,
                sys_getgroups32: ALLOW,
                sys_sched_getaffinity: ALLOW,
                sys_sched_getparam: ALLOW,
                sys_sched_getscheduler: ALLOW,
                sys_sched_get_priority_min: ALLOW,
                sys_sched_get_priority_max: ALLOW,
                sys_sched_setscheduler: ALLOW,
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
                sys_clock_gettime64: ALLOW,
                sys_clock_getres: ALLOW,
                sys_gettimeofday: ALLOW,
                sys_getpid: ALLOW,
                sys_getppid: ALLOW,
                sys_sched_yield: ALLOW,
                sys_clone: ALLOW,
                sys_clone3: ALLOW,
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
                sys_prlimit64: self.handle_prlimit,
                sys_getdents64: ALLOW,
                sys_rseq: ALLOW,
            }
        )

        # FreeBSD-specific syscalls
        if 'freebsd' in sys.platform:
            self.update(
                {
                    sys_mkdir: ACCESS_EPERM,
                    sys_break: ALLOW,
                    sys_sysarch: ALLOW,
                    sys_sysctl: ALLOW,  # TODO: More strict?
                    sys_sysctlbyname: ALLOW,  # TODO: More strict?
                    sys_issetugid: ALLOW,
                    sys_rtprio_thread: ALLOW,  # EPERMs when invalid anyway
                    sys_umtx_op: ALLOW,  # http://fxr.watson.org/fxr/source/kern/kern_umtx.c?v=FREEBSD60#L720
                    sys_getcontext: ALLOW,
                    sys_setcontext: ALLOW,
                    sys_pread: ALLOW,
                    sys_fsync: ALLOW,
                    sys_shm_open: self.handle_open(file_reg=0, flag_reg=1),
                    sys_shm_open2: self.handle_open(file_reg=0, flag_reg=1),
                    sys_cpuset_getaffinity: ALLOW,
                    sys_thr_new: ALLOW,
                    sys_thr_exit: ALLOW,
                    sys_thr_kill: ALLOW,
                    sys_thr_self: ALLOW,
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
                    sys_thr_set_name: ALLOW,
                    sys_sigfastblock: ALLOW,
                    sys_realpathat: self.handle_file_access_at(FilesystemSyscallKind.READ, dir_reg=0, file_reg=1),
                }
            )

    def _compile_fs_jail(self, fs: Sequence[FilesystemAccessRule]) -> FilesystemPolicy:
        return FilesystemPolicy(fs)

    def _dirfd_getter_from_reg(self, reg: int) -> DirFDGetter:
        def getter(debugger: Debugger) -> int:
            return getattr(debugger, 'uarg%d' % reg)

        return getter

    def _dirfd_getter_cwd(self, debugger: Debugger) -> int:
        return AT_FDCWD

    def _fs_jail_getter_from_open_flags_reg(self, reg: int) -> FSJailGetter:
        def getter(debugger: Debugger) -> FilesystemPolicy:
            open_flags = getattr(debugger, 'uarg%d' % reg)
            for flag in open_write_flags:
                # Strict equality is necessary here, since e.g. O_TMPFILE has multiple bits set,
                # and O_DIRECTORY & O_TMPFILE > 0.
                if open_flags & flag == flag:
                    return self.write_fs_jail

            return self.read_fs_jail

        return getter

    def _fs_jail_getter_from_kind(self, kind: FilesystemSyscallKind) -> FSJailGetter:
        def getter(debugger: Debugger) -> FilesystemPolicy:
            return {
                FilesystemSyscallKind.READ: self.read_fs_jail,
                FilesystemSyscallKind.WRITE: self.write_fs_jail,
            }[kind]

        return getter

    def handle_file_access(self, kind: FilesystemSyscallKind, *, file_reg: int) -> AccessChecker:
        return self.access_check(self._fs_jail_getter_from_kind(kind), self._dirfd_getter_cwd, file_reg=file_reg)

    def handle_file_access_at(self, kind: FilesystemSyscallKind, *, dir_reg: int, file_reg: int) -> AccessChecker:
        return self.access_check(
            self._fs_jail_getter_from_kind(kind), self._dirfd_getter_from_reg(dir_reg), file_reg=file_reg
        )

    def handle_open(self, *, file_reg: int, flag_reg: int) -> AccessChecker:
        return self.access_check(
            self._fs_jail_getter_from_open_flags_reg(flag_reg), self._dirfd_getter_cwd, file_reg=file_reg
        )

    def handle_openat(self, *, dir_reg: int, file_reg: int, flag_reg: int) -> AccessChecker:
        return self.access_check(
            self._fs_jail_getter_from_open_flags_reg(flag_reg),
            self._dirfd_getter_from_reg(dir_reg),
            file_reg=file_reg,
        )

    def handle_fstat(self, *, dir_reg: int, file_reg: int) -> AccessChecker:
        def check(debugger: Debugger) -> None:
            rel_file = self.get_rel_file(debugger, reg=file_reg)

            # FIXME(tbrindus): defined here because FreeBSD 13 does not
            # implement AT_EMPTY_PATH, and 14 is not yet released (but does).
            AT_EMPTY_PATH = 0x1000
            # FIXME(tbrindus): we always follow symlinks, regardless of whether
            # AT_SYMLINK_NOFOLLOW is set. This may result in us denying files
            # we otherwise wouldn't have.
            if rel_file == '' and debugger.uarg3 & AT_EMPTY_PATH:
                # If pathname is an empty string, operate on the file referred to
                # by dirfd (which may have been obtained using the open(2) O_PATH
                # flag). In this case, dirfd can refer to any type of file, not
                # just a directory, and the behavior of fstatat() is similar to
                # that of fstat(). If dirfd is AT_FDCWD, the call operates on the
                # current working directory.
                # We already allowed this one way or another, don't check again.
                return

            dirfd = getattr(debugger, 'uarg%d' % dir_reg)
            full_path = self.get_full_path_unnormalized(debugger, rel_file, dirfd=dirfd)
            self._access_check(debugger, full_path, self.read_fs_jail)

        return check

    def access_check(self, fs_jail_getter: FSJailGetter, dirfd_getter: DirFDGetter, *, file_reg: int) -> AccessChecker:
        def check(debugger: Debugger) -> None:
            rel_file = self.get_rel_file(debugger, reg=file_reg)
            dirfd = dirfd_getter(debugger)
            full_path = self.get_full_path_unnormalized(debugger, rel_file, dirfd=dirfd)
            fs_jail = fs_jail_getter(debugger)
            self._access_check(debugger, full_path, fs_jail)

        return check

    def get_rel_file(self, debugger: Debugger, *, reg: int) -> str:
        ptr = getattr(debugger, 'uarg%d' % reg)
        try:
            file = debugger.readstr(ptr)
        except MaxLengthExceeded as e:
            raise DeniedSyscall(ACCESS_ENAMETOOLONG, f'Overly long path: {e.args[0]}')
        except UnicodeDecodeError as e:
            raise DeniedSyscall(
                ACCESS_ENOENT, f'Invalid unicode: {e.object!r}'
            )  # !r for mypy, confirm we know it's bytes

        # Either process called open(NULL, ...), or we failed to read the path
        # in cptbox.  Either way this call should not be allowed; if the path
        # was indeed NULL we can end the request before it gets to the kernel
        # without any downside, and if it was *not* NULL and we failed to read
        # it, then we should *definitely* stop the call here.
        if file is None:
            raise DeniedSyscall(ACCESS_EFAULT, 'Unreadable or NULL path')

        return file

    # intentionally non-normalized
    def get_full_path_unnormalized(self, debugger: Debugger, rel_file: str, *, dirfd: int) -> str:
        if rel_file.startswith('/'):
            return rel_file
        return os.path.join(self.get_dir(debugger, dirfd=dirfd), rel_file)

    def get_dir(self, debugger: Debugger, *, dirfd: int) -> str:
        dirfd = (dirfd & 0x7FFFFFFF) - (dirfd & 0x80000000)  # Interpret dirfd as a signed 32-bit integer
        if dirfd == AT_FDCWD:
            return self._getcwd_pid(debugger.tid)
        return self._getfd_pid(debugger.tid, dirfd)

    def _access_check(self, debugger: Debugger, file: str, fs_jail: FilesystemPolicy) -> None:
        # We want to ensure that if there are symlinks, the user must be able to access both the symlink and
        # its destination. However, we are doing path-based checks, which means we have to check these as
        # as normalized paths. normpath can normalize a path, but also changes the meaning of paths in presence of
        # symlinked directories etc. Therefore, we compare both realpath and normpath and ensure that they refer to
        # the same file, and check the accessibility of both.
        #
        # This works, except when the child process uses /proc/self, which refers to something else in this process.
        # Therefore, we "project" it by changing it to /proc/[tid] for computing the realpath and doing the samefile
        # check. However, we still keep it as /proc/self when checking access rules.

        # normpath doesn't strip leading slashes
        projected = normalized = '/' + os.path.normpath(file).lstrip('/')
        if normalized.startswith('/proc/self'):
            file = os.path.join(f'/proc/{debugger.tid}', os.path.relpath(file, '/proc/self'))
            projected = '/' + os.path.normpath(file).lstrip('/')
        elif normalized.startswith(f'/proc/{debugger.tid}/'):
            # If the child process uses /proc/getpid()/foo, set the normalized path to be /proc/self/foo.
            # Access rules can more easily check /proc/self.
            normalized = os.path.join('/proc/self', os.path.relpath(file, f'/proc/{debugger.tid}'))
        real = os.path.realpath(file)

        try:
            same = normalized == real or os.path.samefile(projected, real)
        except OSError:
            raise DeniedSyscall(ACCESS_ENOENT, f'Cannot stat, file: {file}, projected: {projected}, real: {real}')

        if not same:
            raise DeniedSyscall(
                ACCESS_EACCES, f'Suspected symlink trickery, file: {file}, projected: {projected}, real: {real}'
            )

        if not fs_jail.check(normalized):
            raise DeniedSyscall(ACCESS_EACCES, f'Denying {file}, normalized to {normalized}')

        if normalized != real:
            proc_dir = f'/proc/{debugger.tid}'
            if real.startswith(proc_dir):
                real = os.path.join('/proc/self', os.path.relpath(real, proc_dir))

            if not fs_jail.check(real):
                raise DeniedSyscall(ACCESS_EACCES, f'Denying {file}, real path {real}')

    def handle_kill(self, debugger: Debugger) -> None:
        # Allow tgkill to execute as long as the target thread group is the debugged process
        # libstdc++ seems to use this to signal itself, see <https://github.com/DMOJ/judge/issues/183>
        if debugger.uarg0 != debugger.pid:
            raise DeniedSyscall(ACCESS_EPERM, 'Cannot kill other processes')

    def handle_prlimit(self, debugger: Debugger) -> None:
        if debugger.uarg0 not in (0, debugger.pid):
            raise DeniedSyscall(ACCESS_EPERM, 'Cannot prlimit other processes')

    def handle_prctl(self, debugger: Debugger) -> None:
        PR_GET_DUMPABLE = 3
        PR_SET_NAME = 15
        PR_GET_NAME = 16
        PR_SET_THP_DISABLE = 41
        PR_SET_VMA = 0x53564D41  # Used on Android
        if debugger.arg0 not in (PR_GET_DUMPABLE, PR_SET_NAME, PR_GET_NAME, PR_SET_THP_DISABLE, PR_SET_VMA):
            raise DeniedSyscall(protection_fault, f'Non-whitelisted prctl option: {debugger.arg0}')

    # ignore typing because of overload checks
    def update(self, handlers: Mapping[int, Any]) -> None:  # type: ignore
        for syscall, handler in handlers.items():
            self[syscall] = handler

    def __setitem__(self, syscall: int, handler) -> None:
        if handler == ALLOW or isinstance(handler, ErrnoHandlerCallback):
            super().__setitem__(syscall, handler)
        else:
            super().__setitem__(syscall, wrap_access_check(syscall, handler))


def wrap_access_check(syscall: int, check: AccessChecker) -> HandlerCallback:
    def inner(debugger) -> bool:
        try:
            check(debugger)
            return True
        except DeniedSyscall as failure:
            failure.log(syscall)
            return failure.handler(debugger)

    return inner


def protection_fault(self, debugger: Debugger) -> bool:
    return False


class DeniedSyscall(Exception):
    def __init__(self, handler: Callable, reason: str):
        self.handler = handler
        self.reason = reason

    def log(self, syscall: int):
        syscall_name = by_id[syscall]
        if syscall_name.startswith('sys_'):
            syscall_name = syscall_name[4:]
        # We don't want to put the reason in the first position, because then users could insert format strings.
        log.debug('%s', f'Denied syscall {syscall_name}: ' + self.reason)
