import os
import sys
import time
import resource
import errno
import ctypes
from posix import *
from signal import *


def os_bits():
    return {'AMD64': 64, 'x86_64': 64, 'i386': 32, 'x86': 32}.get(
        os.environ.get("PROCESSOR_ARCHITEW6432", os.environ.get('PROCESSOR_ARCHITECTURE', '')), None)


libc = ctypes.CDLL('libc.so.6', use_errno=True)
ptrace = libc.ptrace

PTRACE_TRACEME = 0
PTRACE_PEEKDATA = 2
PTRACE_GETREGS = 12
PTRACE_SYSCALL = 24
PTRACE_ATTACH = 8
PTRACE_CONT = 7
PTRACE_PEEKUSR = 3

R15 = 0
R14 = 1
R13 = 2
R12 = 3
RBP = 4
RBX = 5
R11 = 6
R10 = 7
R9 = 8
R8 = 9
RAX = 10
RCX = 11
RDX = 12
RSI = 13
RDI = 14
ORIG_RAX = 15
RIP = 16
CS = 17
EFLAGS = 18
RSP = 19
SS = 20
FS_BASE = 21
GS_BASE = 22
DS = 23
ES = 24
FS = 25
GS = 26

sys_read = 0
sys_write = 1
sys_open = 2
sys_close = 3
sys_stat = 4
sys_fstat = 5
sys_mmap = 9
sys_mprotect = 10
sys_munmap = 11
sys_brk = 12
sys_fcntl = 72  # Needed for Java and PHP to run
sys_clone = 56
sys_fork = 57
sys_access = 21
sys_arch_prctl = 158
sys_set_tid_address = 218
sys_set_robust_list = 273
sys_futex = 202
sys_rt_sigaction = 13
sys_rt_sigprocmask = 14
sys_getrlimit = 97
sys_ioctl = 16
sys_readlink = 89
sys_getcwd = 79
sys_geteuid = 107
sys_getuid = 102
sys_getegid = 108
sys_getgid = 104
sys_lstat = 6
sys_openat = 257
sys_getdents = 78

sys_execve = 59

allowed_syscalls = [sys_read,
                    sys_write,
                    sys_open,
                    sys_access,
                    sys_close,
                    sys_stat,
                    sys_fstat,
                    sys_mmap,
                    sys_mprotect,
                    sys_munmap,
                    sys_brk,
                    sys_fcntl,
                    sys_arch_prctl,  # TODO: is this safe?
                    sys_set_tid_address,
                    sys_set_robust_list,
                    sys_futex,
                    sys_rt_sigaction,
                    sys_rt_sigprocmask,
                    sys_getrlimit,
                    sys_ioctl,
                    sys_readlink,
                    sys_getcwd,
                    sys_geteuid,
                    sys_getuid,
                    sys_getegid,
                    sys_getgid,
                    sys_lstat,
                    sys_openat,
                    sys_getdents,

                    sys_clone,
                    sys_fork]

counts = {}

child = sys.argv[1]
args = sys.argv[1:]

rusage = None
status = None

pid = os.fork()
if not pid:
    resource.setrlimit(resource.RLIMIT_AS, (32 * 1024 * 1024,) * 2)
    #resource.setrlimit(resource.RLIMIT_NOFILE, (4, 4))
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
    ptrace(PTRACE_TRACEME, 0, None, None)
    os.kill(os.getpid(), SIGSTOP)
    os.execvp(child, args)
else:
    start = time.time()
    i = 0
    in_syscall = False
    while True:
        __, status, rusage = os.wait4(pid, 0)

        if WIFEXITED(status):
            print "Exited"
            break

        if WIFSIGNALED(status):
            break

        if WSTOPSIG(status) == SIGTRAP:
            in_syscall = not in_syscall
            if in_syscall:
                call = ptrace(PTRACE_PEEKUSR, pid, 8 * ORIG_RAX, None)

                counts[call] = counts.get(call, 0) + 1
                print "%d: %s" % (call, counts)

                if call == sys_execve:
                    # execve is called twice: once when we os.execvp(child, args),
                    # and once when the child actually spawns
                    # anything after these two calls is likely malicious
                    if 0 and counts[sys_execve] > 2:
                        raise Exception("YOU MOTHERFORKER")
                elif call not in allowed_syscalls:
                    raise Exception(call)

        ptrace(PTRACE_SYSCALL, pid, None, None)

    duration = time.time() - start
    if status is None:  # TLE
        os.kill(pid, SIGKILL)
        _, status, rusage = os.wait4(pid, 0)
        print 'Time Limit Exceeded'
    print rusage.ru_maxrss, 'KB of RAM'
    print 'Execution time: %.3f seconds' % duration
    print 'Return:', os.WEXITSTATUS(status)

