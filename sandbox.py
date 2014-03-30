import os
import sys
import time
import resource
import errno
import ctypes
from signal import *
from ptrace import *

if __name__ == "__main__":
    proc_mem = None
    do_allow = lambda: True


    def do_write():
        fd = arg0(pid)
        # Only allow writing to stdout & stderr
        print fd,
        return fd == 1 or fd == 2


    execve_count = 0

    def do_execve():
        global execve_count
        execve_count += 1
        if execve_count > 2:
            return False
        return True

    def do_access():
        global proc_mem
        try:
            addr = ctypes.c_uint(arg0(pid)).value
            print "(%d)" % addr,
            if addr > 0:
                if not proc_mem:
                    proc_mem = open("/proc/%d/mem" % pid, "rb")
                proc_mem.seek(addr, 0)
                buf = ''
                page = (addr + 4096) // 4096 * 4096 - addr
                while True:
                    buf += proc_mem.read(page)
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

    def do_open():
        mode = ctypes.c_size_t(arg2(pid)).value
        if mode:
            print mode,
            # TODO: return False
        return do_access()

    # @formatter:off
    proxied_syscalls = {
        sys_execve:             do_execve,
        sys_read:               do_allow,
        sys_write:              do_write,
        sys_open:               do_open,
        sys_access:             do_access,
        sys_close:              do_allow,
        sys_stat:               do_allow,
        sys_fstat:              do_allow,
        sys_mmap:               do_allow,
        sys_mprotect:           do_allow,
        sys_munmap:             do_allow,
        sys_brk:                do_allow,
        sys_fcntl:              do_allow,
        sys_arch_prctl:         do_allow,  # TODO: is this safe?
        sys_set_tid_address:    do_allow,
        sys_set_robust_list:    do_allow,
        sys_futex:              do_allow,
        sys_rt_sigaction:       do_allow,
        sys_rt_sigprocmask:     do_allow,
        sys_getrlimit:          do_allow,
        sys_ioctl:              do_allow,
        sys_readlink:           do_allow,
        sys_getcwd:             do_allow,
        sys_geteuid:            do_allow,
        sys_getuid:             do_allow,
        sys_getegid:            do_allow,
        sys_getgid:             do_allow,
        sys_lstat:              do_allow,
        sys_openat:             do_allow,
        sys_getdents:           do_allow,
        sys_lseek:              do_allow,

        sys_clone:              do_allow,
        sys_exit_group:         do_allow,
    }
    # @formatter:on

    child = sys.argv[1]
    args = sys.argv[1:]

    rusage = None
    status = None

    mem = None
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
                    call = get_syscall_number(pid)

                    print syscall_to_string(call),

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

