import struct
import sys

from dmoj.cptbox._cptbox import AT_FDCWD, Debugger
from dmoj.cptbox.filesystem_policies import ExactFile, FilesystemPolicy, RecursiveDir
from dmoj.cptbox.handlers import ACCESS_EFAULT, ACCESS_EPERM, ALLOW
from dmoj.cptbox.isolate import DeniedSyscall, FilesystemSyscallKind, IsolateTracer
from dmoj.cptbox.syscalls import *
from dmoj.cptbox.tracer import AdvancedDebugger
from dmoj.executors.base_executor import BASE_FILESYSTEM, BASE_WRITE_FILESYSTEM


UTIME_OMIT = (1 << 30) - 2


class CompilerIsolateTracer(IsolateTracer):
    def __init__(self, *, tmpdir, read_fs, write_fs):
        read_fs += BASE_FILESYSTEM + [
            RecursiveDir(tmpdir),
            ExactFile('/bin/strip'),
            RecursiveDir('/usr/x86_64-linux-gnu'),
        ]
        write_fs += BASE_WRITE_FILESYSTEM + [RecursiveDir(tmpdir)]
        super().__init__(read_fs=read_fs, write_fs=write_fs)

        self.update(
            {
                # Process spawning system calls
                sys_fork: ALLOW,
                sys_vfork: ALLOW,
                sys_execve: ALLOW,
                sys_getcpu: ALLOW,
                sys_getpgid: ALLOW,
                # Directory system calls
                sys_mkdir: self.handle_file_access(FilesystemSyscallKind.WRITE, file_reg=0),
                sys_mkdirat: self.handle_file_access_at(FilesystemSyscallKind.WRITE, dir_reg=0, file_reg=1),
                sys_rmdir: self.handle_file_access(FilesystemSyscallKind.WRITE, file_reg=0),
                # Linking system calls
                sys_link: self.handle_file_access(FilesystemSyscallKind.WRITE, file_reg=1),
                sys_linkat: self.handle_file_access_at(FilesystemSyscallKind.WRITE, dir_reg=2, file_reg=3),
                sys_unlink: self.handle_file_access(FilesystemSyscallKind.WRITE, file_reg=0),
                sys_unlinkat: self.handle_file_access_at(FilesystemSyscallKind.WRITE, dir_reg=0, file_reg=1),
                sys_symlink: self.handle_file_access(FilesystemSyscallKind.WRITE, file_reg=1),
                # Miscellaneous other filesystem system calls
                sys_chdir: self.handle_file_access(FilesystemSyscallKind.READ, file_reg=0),
                sys_chmod: self.handle_file_access(FilesystemSyscallKind.WRITE, file_reg=0),
                sys_utimensat: self.do_utimensat,
                sys_umask: ALLOW,
                sys_flock: ALLOW,
                sys_fsync: ALLOW,
                sys_fadvise64: ALLOW,
                sys_fchmodat: self.handle_file_access_at(FilesystemSyscallKind.WRITE, dir_reg=0, file_reg=1),
                sys_fchmod: self.handle_fchmod,
                sys_fallocate: ALLOW,
                sys_ftruncate: ALLOW,
                sys_rename: self.handle_rename,
                sys_renameat: self.handle_renameat,
                # I/O system calls
                sys_readv: ALLOW,
                sys_pwrite64: ALLOW,
                sys_sendfile: ALLOW,
                # Event loop system calls
                sys_epoll_create: ALLOW,
                sys_epoll_create1: ALLOW,
                sys_epoll_ctl: ALLOW,
                sys_epoll_wait: ALLOW,
                sys_epoll_pwait: ALLOW,
                sys_timerfd_settime: ALLOW,
                sys_eventfd2: ALLOW,
                sys_waitid: ALLOW,
                sys_wait4: ALLOW,
                # Network system calls, we don't sandbox these
                sys_socket: ALLOW,
                sys_socketpair: ALLOW,
                sys_connect: ALLOW,
                sys_setsockopt: ALLOW,
                sys_getsockname: ALLOW,
                sys_sendmmsg: ALLOW,
                sys_recvfrom: ALLOW,
                sys_sendto: ALLOW,
                # Miscellaneous other system calls
                sys_msync: ALLOW,
                sys_clock_nanosleep: ALLOW,
                sys_memfd_create: ALLOW,
                sys_rt_sigsuspend: ALLOW,
            }
        )

        # FreeBSD-specific syscalls
        if 'freebsd' in sys.platform:
            self.update(
                {
                    sys_rfork: ALLOW,
                    sys_procctl: ALLOW,
                    sys_cap_rights_limit: ALLOW,
                    sys_posix_fadvise: ALLOW,
                    sys_posix_fallocate: ALLOW,
                    sys_setrlimit: ALLOW,
                    sys_cap_ioctls_limit: ALLOW,
                    sys_cap_fcntls_limit: ALLOW,
                    sys_cap_enter: ALLOW,
                    sys_utimes: self.handle_file_access(FilesystemSyscallKind.WRITE, file_reg=0),
                }
            )

    def handle_rename(self, debugger: Debugger) -> None:
        self.access_check(self._write_fs_jail_getter, self._dirfd_getter_cwd, file_reg=0)(debugger)
        self.access_check(self._write_fs_jail_getter, self._dirfd_getter_cwd, file_reg=1)(debugger)

    def handle_renameat(self, debugger: Debugger) -> None:
        self.access_check(self._write_fs_jail_getter, self._dirfd_getter_from_reg(0), file_reg=1)(debugger)
        self.access_check(self._write_fs_jail_getter, self._dirfd_getter_from_reg(2), file_reg=3)(debugger)

    def _write_fs_jail_getter(self, debugger: Debugger) -> FilesystemPolicy:
        return self.write_fs_jail

    def do_utimensat(self, debugger: AdvancedDebugger) -> None:
        timespec = struct.Struct({32: '=ii', 64: '=QQ'}[debugger.address_bits])

        # Emulate https://github.com/torvalds/linux/blob/v5.14/fs/utimes.c#L152-L161
        times_ptr = debugger.uarg2
        if times_ptr:
            try:
                buffer = debugger.readbytes(times_ptr, timespec.size * 2)
            except OSError:
                raise DeniedSyscall(ACCESS_EFAULT, f'Cannot read from times_ptr: {times_ptr}')

            times = list(timespec.iter_unpack(buffer))
            if times[0][1] == UTIME_OMIT and times[1][1] == UTIME_OMIT:
                debugger.syscall = -1

                def on_return():
                    debugger.result = 0

                debugger.on_return(on_return)

        else:
            # Emulate https://github.com/torvalds/linux/blob/v5.14/fs/utimes.c#L142-L143
            if debugger.uarg0 != AT_FDCWD and not debugger.uarg1:
                path = self._getfd_pid(debugger.tid, debugger.uarg0)
                if not self.write_fs_jail.check(path):
                    raise DeniedSyscall(ACCESS_EPERM, f'Denying access to {path}')
            else:
                return self.handle_file_access_at(FilesystemSyscallKind.WRITE, dir_reg=0, file_reg=1)(debugger)

    def handle_fchmod(self, debugger: Debugger) -> None:
        path = self._getfd_pid(debugger.tid, debugger.uarg0)
        if not self.write_fs_jail.check(path):
            raise DeniedSyscall(ACCESS_EPERM, f'Denying access to {path}')
