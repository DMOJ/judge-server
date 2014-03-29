import os
import sys
import time
import resource
import errno
import ctypes
from signal import *

libc = ctypes.CDLL('libc.so.6', use_errno=True)
ptrace = libc.ptrace

# ptrace constants
PTRACE_TRACEME = 0
PTRACE_PEEKDATA = 2
PTRACE_GETREGS = 12
PTRACE_SYSCALL = 24
PTRACE_ATTACH = 8
PTRACE_CONT = 7
PTRACE_PEEKUSR = 3
PTRACE_PEEKDATA = 2

# x64 registers
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

# syscall ids
# @formatter:off
calls = {
    'sys_read':             0,
    'sys_write':            1,
    'sys_open':             2,
    'sys_close':            3,
    'sys_stat':             4,
    'sys_fstat':            5,
    'sys_mmap':             9,
    'sys_mprotect':         10,
    'sys_munmap':           11,
    'sys_brk':              12,
    'sys_fcntl':            72,  # Needed for Java and PHP to run
    'sys_clone':            56,
    'sys_fork':             57,
    'sys_access':           21,
    'sys_arch_prctl':       158,
    'sys_set_tid_address':  218,
    'sys_set_robust_list':  273,
    'sys_futex':            202,
    'sys_rt_sigaction':     13,
    'sys_rt_sigprocmask':   14,
    'sys_getrlimit':        97,
    'sys_ioctl':            16,
    'sys_readlink':         89,
    'sys_getcwd':           79,
    'sys_geteuid':          107,
    'sys_getuid':           102,
    'sys_getegid':          108,
    'sys_getgid':           104,
    'sys_lstat':            6,
    'sys_openat':           257,
    'sys_getdents':         78,
    'sys_lseek':            8,

    'sys_execve':           59
}
# @formatter:on

# Define all syscalls as variables
for call, id in calls.iteritems():
    vars()[call] = id


def call_to_string(call):
    for v, val in calls.iteritems():
        if val == call:
            return v
    return "unknown"

rdi = lambda: ctypes.c_long(ptrace(PTRACE_PEEKUSR, pid, 8 * RDI, None)).value

__allow = lambda: True


def __do_write():
    fd = rdi()
    # Only allow writing to stdout & stderr
    print fd,
    return fd == 1 or fd == 2

__execve_count = 0
def __do_execve():
    global __execve_count
    __execve_count += 1
    if __execve_count > 2:
        return False
    return True

def __open():
    try:
        addr = rdi()

        print "(%d)" % addr,
        if addr > 0:
            mem = open("/proc/%d/mem" % pid, "rb")
            mem.seek(addr, 0)
            buf = ''
            page = (addr + 4096) // 4096 * 4096 - addr
            while True:
                buf += mem.read(page)
                if '\0' in buf:
                    buf = buf[:buf.index('\0')]
                    break
                page = 4096
            print buf,
            for file in ["/usr/bin/python"]:
                if buf.startswith(file):
                    break
            else:
                return True

    except:
        import traceback
        traceback.print_exc()
    return True

# @formatter:off
proxied_syscalls = {
    sys_execve:             __do_execve,
    sys_read:               __allow,
    sys_write:              __do_write,
    sys_open:               __open,
    sys_access:             __open,
    sys_close:              __allow,
    sys_stat:               __allow,
    sys_fstat:              __allow,
    sys_mmap:               __allow,
    sys_mprotect:           __allow,
    sys_munmap:             __allow,
    sys_brk:                __allow,
    sys_fcntl:              __allow,
    sys_arch_prctl:         __allow,  # TODO: is this safe?
    sys_set_tid_address:    __allow,
    sys_set_robust_list:    __allow,
    sys_futex:              __allow,
    sys_rt_sigaction:       __allow,
    sys_rt_sigprocmask:     __allow,
    sys_getrlimit:          __allow,
    sys_ioctl:              __allow,
    sys_readlink:           __allow,
    sys_getcwd:             __allow,
    sys_geteuid:            __allow,
    sys_getuid:             __allow,
    sys_getegid:            __allow,
    sys_getgid:             __allow,
    sys_lstat:              __allow,
    sys_openat:             __allow,
    sys_getdents:           __allow,
    sys_lseek:              __allow,

    sys_clone:              __allow,
    #sys_fork:               __allow
}
# @formatter:on

child = sys.argv[1]
args = sys.argv[1:]

rusage = None
status = None

pid = os.fork()
if not pid:
    resource.setrlimit(resource.RLIMIT_AS, (32 * 1024 * 1024,) * 2)
    ptrace(PTRACE_TRACEME, 0, None, None)
    os.kill(os.getpid(), SIGSTOP)
    os.execvp(child, args)
else:
    start = time.time()
    i = 0
    in_syscall = False
    while True:
        __, status, rusage = os.wait4(pid, 0)

        if os.WIFEXITED(status):
            print "Exited"
            break

        if os.WIFSIGNALED(status):
            break

        if os.WSTOPSIG(status) == SIGTRAP:
            if in_syscall:
                call = ptrace(PTRACE_PEEKUSR, pid, 8 * ORIG_RAX, None)

                print call_to_string(call),

                if call in proxied_syscalls:
                    if not proxied_syscalls[call]():
                        os.kill(pid, SIGKILL)
                        print
                        print "You're doing Something Bad"
                        break
                else:
                    print
                    raise Exception(call)
                print
            in_syscall = not in_syscall

        ptrace(PTRACE_SYSCALL, pid, None, None)

    duration = time.time() - start
    if status is None:  # TLE
        os.kill(pid, SIGKILL)
        _, status, rusage = os.wait4(pid, 0)
        print 'Time Limit Exceeded'
    print rusage.ru_maxrss + rusage.ru_isrss, 'KB of RAM'
    print 'Execution time: %.3f seconds' % duration
    print 'Return:', os.WEXITSTATUS(status)

