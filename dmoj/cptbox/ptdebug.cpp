#define _BSD_SOURCE
#include <assert.h>
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

#if !PTBOX_FREEBSD
#include <elf.h>
#endif

pt_debugger::pt_debugger() {}

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
    _bsd_syscall = info->pl_syscall_code;
}

void pt_debugger::setpid(pid_t pid) {
    this->tid = pid;
}
#else
void pt_debugger::tid_reset(pid_t tid) {
    syscall_[tid] = 0;
}

void pt_debugger::settid(pid_t tid) {
    this->tid = tid;
    if (!process->use_seccomp()) {
        // All seccomp syscall events are enter events
        if (!syscall_.count(tid)) syscall_[tid] = 0;
        syscall_[tid] ^= 1;
    }
}
#endif

int pt_debugger::pre_syscall() {
    int err;
#if PTBOX_FREEBSD
    if (ptrace(PT_GETREGS, tid, (caddr_t) &regs, 0)) {
        err = errno;
        perror("ptrace(PT_GETREGS)");
#else
    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = sizeof regs;

    if (ptrace(PTRACE_GETREGSET, tid, NT_PRSTATUS, &iovec)) {
        err = errno;
        perror("ptrace(PTRACE_GETREGSET)");
#endif
        abi_ = PTBOX_ABI_INVALID;
        return err;
    } else {
#if PTBOX_FREEBSD
        abi_ = abi_from_reg_size(sizeof regs);
#else
        abi_ = abi_from_reg_size(iovec.iov_len);
#endif
        regs_changed = false;
        return 0;
    }
}

int pt_debugger::post_syscall() {
    // Should not be possible because pt_process should already have generated a protection fault.
    assert(abi_ != PTBOX_ABI_INVALID);
    if (!regs_changed)
        return 0;

    int err;
#if PTBOX_FREEBSD
    if (ptrace(PT_SETREGS, tid, (caddr_t) &regs, 0)) {
        err = errno;
        perror("ptrace(PTRACE_SETREGSET)");
#else
    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = sizeof regs;
    if (ptrace(PTRACE_SETREGSET, tid, NT_PRSTATUS, &iovec)) {
        err = errno;
        perror("ptrace(PTRACE_SETREGSET)");
#endif
        return err;
    }
    return 0;
}

#if !PTBOX_FREEBSD
long pt_debugger::error() {
    long res = result();
    return res >= -4096 && res < 0 ? -res : 0;
}

void pt_debugger::error(long value) {
    result(-value);
}
#endif

#if PTBOX_FREEBSD
typedef int ptrace_read_t;
#else
typedef long ptrace_read_t;

#if __BIONIC__
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
#endif  // __BIONIC__

#endif

char *pt_debugger::readstr(unsigned long addr, size_t max_size) {
    if (!addr) {
        return nullptr;
    }

#if PTBOX_FREEBSD
    return readstr_peekdata(addr, max_size);
#else
    static unsigned long page_size = sysconf(_SC_PAGESIZE);
    static unsigned long page_mask = (unsigned long) -page_size;

    char *buf;
    unsigned long remain, read = 0;
    struct iovec local, remote;

    if (use_peekdata) {
        return readstr_peekdata(addr, max_size);
    }

    remain = ((addr + page_size) & page_mask) - addr;
    buf = (char *) malloc(max_size + 1);

    if (!buf) {
        return nullptr;
    }

    while (read < max_size) {
        local.iov_base = (void *) (buf + read);
        local.iov_len = remain;
        remote.iov_base = (void *) (addr + read);
        remote.iov_len = remain;

        // The man page guarantees that a partial read cannot happen at
        // sub-iovec granularity, so we don't need to retry here.
        if (process_vm_readv(tid, &local, 1, &remote, 1, 0) > 0) {
            if (memchr(buf + read, '\0', remain)) {
                return buf;
            }

            read += remain;
        } else {
            perror("process_vm_readv");
            free(buf);

            char *result = readstr_peekdata(addr, max_size);
            // This means process_vm_readv failed but peekdata succeeded.
            // We should just give up on process_vm_readv.
            if (!read && result) {
                use_peekdata = true;
            }
            return result;
        }

        remain = page_size < max_size - read ? page_size : max_size - read;
    }

    buf[max_size] = '\0';
    return buf;
#endif
}

char *pt_debugger::readstr_peekdata(unsigned long addr, size_t max_size) {
    size_t size = 4096, read = 0;
    char *buf = (char *) malloc(size);

    if (!buf || !addr) {
        return nullptr;
    }

    union {
        ptrace_read_t val;
        char byte[sizeof(ptrace_read_t)];
    } data;

    while (true) {
        // Re-alloc buffer in case next read would overflow the buffer.
        if (read + sizeof(ptrace_read_t) > size) {
            if (size > max_size) {
                buf[max_size] = '\0';
                break;
            }

            size += 4096;
            if (size > max_size) {
                size = max_size + 1;
            }

            void *nbuf = realloc(buf, size);
            if (!nbuf) {
                perror("realloc");
                free(buf);
                return nullptr;
            }

            buf = (char *) nbuf;
        }

        errno = 0;
#if PTBOX_FREEBSD
        // TODO: we could use PT_IO to speed up this entire function by reading
        // chunks rather than bytes
        data.val = ptrace(PT_READ_D, tid, (caddr_t) (addr + read), 0);
#else
        data.val = ptrace(PTRACE_PEEKDATA, tid, addr + read, NULL);
#endif
        if (data.val == -1 && errno) {
            // It would be unsafe to continue, so bail out.
            perror("ptrace(PTRACE_PEEKDATA)");
            free(buf);
            return nullptr;
        }

        memcpy(buf + read, data.byte, sizeof(ptrace_read_t));
        if (has_null(data.byte, sizeof(ptrace_read_t))) {
            break;
        }

        read += sizeof(ptrace_read_t);
    }

    return buf;
}

void pt_debugger::freestr(char *buf) {
    free(buf);
}
