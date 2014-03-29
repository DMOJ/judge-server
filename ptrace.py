import ctypes

read_reg = lambda pid, reg: ctypes.c_long(ptrace(PTRACE_PEEKUSR, pid, 8 * reg, None)).value
arg0 = lambda pid: read_reg(pid, RDI)
arg1 = lambda pid: read_reg(pid, RSI)
arg2 = lambda pid: read_reg(pid, RDX)
arg3 = lambda pid: read_reg(pid, R10)
arg4 = lambda pid: read_reg(pid, R8)
arg5 = lambda pid: read_reg(pid, R9)

get_syscall_number = lambda pid: ptrace(PTRACE_PEEKUSR, pid, 8 * ORIG_RAX, None)

# syscall ids
# @formatter:off
syscalls = {
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
for call, id in syscalls.iteritems():
    vars()[call] = id


def syscall_to_string(call):
    for v, val in syscalls.iteritems():
        if val == call:
            return v
    return "unknown"


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