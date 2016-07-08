import re
import sys
import os

from dmoj.cptbox.handlers import ALLOW, STDOUTERR, ACCESS_DENIED
from dmoj.cptbox.syscalls import *


class CHROOTSecurity(dict):
    def __init__(self, filesystem, writable=(1, 2), io_redirects=None):
        super(CHROOTSecurity, self).__init__()
        self.fs_jail = re.compile('|'.join(filesystem) if filesystem else '^')
        self._writable = list(writable)
        self._io_redirects = io_redirects

        self.update({
            sys_read: ALLOW,
            sys_write: STDOUTERR if writable == (1, 2) and not io_redirects else self.do_write,
            sys_writev: self.do_write,
            sys_open: self.do_open,
            sys_access: self.do_access,
            sys_faccessat: self.do_faccessat,
            # Deny with report
            sys_mkdir: self.deny_with_file_path('mkdir', 0),
            sys_tgkill: self.do_tgkill,
            sys_prctl: self.do_prctl,

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
            sys_openat: ALLOW,
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

            # FreeBSD specific
            sys_obreak: ALLOW,
            sys_sysarch: ALLOW,
            sys_thr_self: ALLOW,
        })

        # FreeBSD-specific syscalls
        if 'freebsd' in sys.platform:
            self.update({
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
            })

    def deny_with_file_path(self, syscall, argument):
        def check(debugger):
            file = debugger.readstr(getattr(debugger, 'uarg%d' % argument))
            print>> sys.stderr, '%s: not allowed to access: %s' % (syscall, file)
            return False

        return check

    def do_write(self, debugger):
        return debugger.arg0 in self._writable

    def do_access(self, debugger):
        file = debugger.readstr(debugger.uarg0)
        return self._file_access_check(file)

    def do_open(self, debugger):
        file_ptr = debugger.uarg0
        file = debugger.readstr(file_ptr)

        if self._io_redirects:
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

        return self._file_access_check(file)

    def _file_access_check(self, file):
        if self.fs_jail.match(file) is None:
            print>> sys.stderr, 'Not allowed to access:', file
            return False
        return True

    def do_faccessat(self, debugger):
        file = debugger.readstr(debugger.uarg1)
        if self.fs_jail.match(file) is None:
            print>> sys.stderr, 'Not allowed to access:', file
            return False
        return True

    def do_tgkill(self, debugger):
        tgid = debugger.uarg0

        # Allow tgkill to execute as long as the target thread group is the debugged process
        # libstdc++ seems to use this to signal itself, see <https://github.com/DMOJ/judge/issues/183>
        return tgid == debugger.pid

    def do_prctl(self, debugger):
        # PR_SET_NAME = 15
        return debugger.arg0 in (15,)
