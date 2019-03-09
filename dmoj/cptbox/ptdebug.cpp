#define _BSD_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/ptrace.h>
#include <sys/uio.h>
#include <unistd.h>
#include "ptbox.h"

pt_debugger::pt_debugger() : on_return_callback(NULL) {}

#if PTBOX_FREEBSD
    bool pt_debugger::use_peekdata = true;
#else
    bool pt_debugger::use_peekdata = false;
#endif

bool has_null(char *buf, unsigned long size) {
    for (unsigned long i = 0; i < size; ++i) {
        if (buf[i] == '\0')
            return true;
    }
    return false;
}

void pt_debugger::set_process(pt_process *proc) {
    process = proc;
}

void pt_debugger::new_process() {
#if PTBOX_FREEBSD
    tid = process->getpid();
#endif
}

#if PTBOX_FREEBSD
void pt_debugger::update_syscall(struct ptrace_lwpinfo *info) {
    struct reg bsd_regs;
    ptrace(PT_GETREGS, tid, (caddr_t) &bsd_regs, 0);
    map_regs_to_linux(&bsd_regs, &bsd_converted_regs);

    if (info->pl_flags & PL_FLAG_SCX)
        bsd_converted_regs.orig_rax = syscall_[info->pl_lwpid];
        // Not available on all kernels.
        // bsd_converted_regs.orig_rax = info->pl_syscall_code;
    else if (info->pl_flags & PL_FLAG_SCE)
        syscall_[info->pl_lwpid] = bsd_converted_regs.rax;
}

void pt_debugger::setpid(pid_t pid) {
    this->tid = pid;
}
#else
void pt_debugger::settid(pid_t tid) {
    this->tid = tid;
#if !PTBOX_SECCOMP // All seccomp syscall events are enter events
    if (!syscall_.count(tid)) syscall_[tid] = 0;
    syscall_[tid] ^= 1;
#endif
}
#endif

void pt_debugger::pre_syscall() {}
void pt_debugger::post_syscall() {}

long pt_debugger::peek_reg(int idx) {
#if PTBOX_FREEBSD
    return ((reg_type*)&bsd_converted_regs)[idx];
#else
    long res;
    errno = 0;
    res = ptrace(PTRACE_PEEKUSER, tid, sizeof(long) * idx, 0);
    if (res == -1 && errno)
        perror("ptrace(PTRACE_PEEKUSER)");
    return res;
#endif
}

void pt_debugger::poke_reg(int idx, long data) {
#if PTBOX_FREEBSD
    ((reg_type*)&bsd_converted_regs)[idx] = data;

    struct reg bsd_regs;

    // Update bsd_regs with latest regs, since not all are mapped by map_regs_from_linux and we don't want
    // garbage to be written to the other registers.
    // Alternatively we could be mapping them in map_regs, but that'd be more fragile and less easy (there are
    // some registers, like r_trapno on FreeBSD, that have no real equivalent on Linux, and vice-versa).
    ptrace(PT_GETREGS, tid, (caddr_t) &bsd_regs, 0);

    map_regs_from_linux(&bsd_regs, &bsd_converted_regs);
    ptrace(PT_SETREGS, tid, (caddr_t) &bsd_regs, 0);
#else
    ptrace(PTRACE_POKEUSER, tid, sizeof(long) * idx, data);
#endif
}

#if PTBOX_FREEBSD
typedef int ptrace_read_t;
#else
typedef long ptrace_read_t;

#ifndef SYS_process_vm_readv
#define SYS_process_vm_readv 270
#endif

// Android's bionic C library doesn't have this system call wrapper.
// Therefore, we use a weak symbol so it could be used when it doesn't exist.
ssize_t __attribute__((weak)) process_vm_readv(
    pid_t pid, const struct iovec *lvec, unsigned long liovcnt,
    const struct iovec *rvec, unsigned long riovcnt, unsigned long flags
) {
    return syscall(SYS_process_vm_readv, (long) pid, lvec, liovcnt, rvec, riovcnt, flags);
}
#endif

char *pt_debugger::readstr(unsigned long addr, size_t max_size) {
#if PTBOX_FREEBSD
    return readstr_peekdata(addr, max_size);
#else
    static unsigned long page_size = sysconf(_SC_PAGESIZE);
    static unsigned long page_mask = (unsigned long) -page_size;

    char *buf;
    unsigned long remain, read = 0;
    struct iovec local, remote;

    if (use_peekdata)
        return readstr_peekdata(addr, max_size);

    remain = addr - (addr & page_mask);
    buf = (char *) malloc(max_size + 1);

    while (read < max_size) {
        local.iov_base = (void *) (buf + read);
        local.iov_len = remain;
        remote.iov_base = (void *) (addr + read);
        remote.iov_len = remain;

        errno = 0;
        if (process_vm_readv(tid, &local, 1, &remote, 1, 0) > 0) {
            if (memchr(buf + read, '\0', remain))
                return buf;
            read += remain;
        } else if (errno == ENOSYS || errno == EPERM) {
            perror("process_vm_readv");
            use_peekdata = true;
            free(buf);
            return readstr_peekdata(addr, max_size);
        } else if (!errno) {
            buf[read] = 0;
            return buf;
        } else {
            if (errno != EFAULT && errno != EIO && errno != EBADF)
                perror("process_vm_readv");
            free(buf);

            char *result = readstr_peekdata(addr, max_size);
            // This means process_vm_readv failed but peekdata succeeded.
            // We should just give up on process_vm_readv.
            if (!read && result && *result)
                use_peekdata = true;
            return result;
        }
        remain = page_size < max_size - read ? page_size : max_size - read;
    }
    buf[max_size] = 0;
    return buf;
#endif
}

char *pt_debugger::readstr_peekdata(unsigned long addr, size_t max_size) {
    size_t size = 4096, read = 0;
    char *buf = (char *) malloc(size);
    union {
        ptrace_read_t val;
        char byte[sizeof(ptrace_read_t)];
    } data;

    while (true) {
        if (read + sizeof(ptrace_read_t) > size) {
            if (max_size && size >= max_size) {
                buf[max_size-1] = 0;
                break;
            }

            size += 4096;
            if (max_size && size > max_size)
                size = max_size;

            void *nbuf = realloc(buf, size);
            if (!nbuf) {
                buf[size-4097] = 0;
                break;
            }
            buf = (char *) nbuf;
        }
#if PTBOX_FREEBSD
        // TODO: we could use PT_IO to speed up this entire function by reading chunks rather than byte
        data.val = ptrace(PT_READ_D, tid, (caddr_t) (addr + read), 0);
#else
        errno = 0;
        data.val = ptrace(PTRACE_PEEKDATA, tid, addr + read, NULL);
        if (data.val == -1 && errno)
            perror("ptrace(PTRACE_PEEKDATA)");
#endif
        memcpy(buf + read, data.byte, sizeof(ptrace_read_t));
        if (has_null(data.byte, sizeof(ptrace_read_t)))
            break;
        read += sizeof(ptrace_read_t);
    }
    return buf;
}

void pt_debugger::freestr(char *buf) {
    free(buf);
}

pt_debugger::~pt_debugger() {}
