import os
import sys
import time
import resource
import errno
import ctypes
from posix import *
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


allow = lambda: True


def do_write():
    fd = ptrace(PTRACE_PEEKUSR, pid, 8 * RDI, None)
    print fd
    # Only allow writing to stdout & stderr
    return fd == 1 or fd == 2

__execve_count = 0
def do_execve():
    global __execve_count
    __execve_count += 1
    if __execve_count > 2:
        return False
    return True

# @formatter:off
proxied_syscalls = {
    sys_execve:             do_execve,
    sys_read:               allow,
    sys_write:              do_write,
    sys_open:               allow,
    sys_access:             allow,
    sys_close:              allow,
    sys_stat:               allow,
    sys_fstat:              allow,
    sys_mmap:               allow,
    sys_mprotect:           allow,
    sys_munmap:             allow,
    sys_brk:                allow,
    sys_fcntl:              allow,
    sys_arch_prctl:         allow,  # TODO: is this safe?
    sys_set_tid_address:    allow,
    sys_set_robust_list:    allow,
    sys_futex:              allow,
    sys_rt_sigaction:       allow,
    sys_rt_sigprocmask:     allow,
    sys_getrlimit:          allow,
    sys_ioctl:              allow,
    sys_readlink:           allow,
    sys_getcwd:             allow,
    sys_geteuid:            allow,
    sys_getuid:             allow,
    sys_getegid:            allow,
    sys_getgid:             allow,
    sys_lstat:              allow,
    sys_openat:             allow,
    sys_getdents:           allow,
    sys_lseek:              allow,

    sys_clone:              allow,
    sys_fork:               allow
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

        if WIFEXITED(status):
            print "Exited"
            break

        if WIFSIGNALED(status):
            break

        if WSTOPSIG(status) == SIGTRAP:
            if in_syscall:
                call = ptrace(PTRACE_PEEKUSR, pid, 8 * ORIG_RAX, None)

                print call_to_string(call)

                if call in proxied_syscalls:
                    if not proxied_syscalls[call]():
                        os.kill(pid, SIGKILL)
                        print "You're doing Something Bad"
                else:
                    raise Exception(call)
            in_syscall = not in_syscall

        ptrace(PTRACE_SYSCALL, pid, None, None)

    duration = time.time() - start
    if status is None:  # TLE
        os.kill(pid, SIGKILL)
        _, status, rusage = os.wait4(pid, 0)
        print 'Time Limit Exceeded'
    print rusage.ru_maxrss, 'KB of RAM'
    print 'Execution time: %.3f seconds' % duration
    print 'Return:', os.WEXITSTATUS(status)

