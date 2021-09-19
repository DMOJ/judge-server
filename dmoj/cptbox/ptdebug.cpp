#define _DEFAULT_SOURCE
#define _BSD_SOURCE

#include "ptbox.h"
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <unistd.h>

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
ssize_t __attribute__((weak)) process_vm_readv(pid_t pid, const struct iovec *lvec, unsigned long liovcnt,
                                               const struct iovec *rvec, unsigned long riovcnt, unsigned long flags) {
    return syscall(SYS_process_vm_readv, (long) pid, lvec, liovcnt, rvec, riovcnt, flags);
}
#endif  // __BIONIC__

#endif

char *pt_debugger::readstr(unsigned long addr, size_t max_size) {
    if (!addr) {
        return nullptr;
    }

    static unsigned long page_size = sysconf(_SC_PAGESIZE);
    static unsigned long page_mask = (unsigned long) -page_size;

    char *buf;
    unsigned long remain, read = 0;

    if (use_peekdata) {
        return readstr_peekdata(addr, max_size);
    }

    remain = ((addr + page_size) & page_mask) - addr;
    buf = (char *) malloc(max_size + 1);

    if (!buf) {
        return nullptr;
    }

    while (read < max_size) {
#if !PTBOX_FREEBSD
        struct iovec local, remote;
        local.iov_base = (void *) (buf + read);
        local.iov_len = remain;
        remote.iov_base = (void *) (addr + read);
        remote.iov_len = remain;

        // The man page guarantees that a partial read cannot happen at
        // sub-iovec granularity, so we don't need to retry here.
        if (process_vm_readv(tid, &local, 1, &remote, 1, 0) > 0) {
#else
        struct ptrace_io_desc iod = {
            .piod_op = PIOD_READ_D,
            .piod_offs = (void *) (addr + read),
            .piod_addr = (void *) (buf + read),
            .piod_len = remain,
        };

        if (ptrace(PT_IO, tid, (caddr_t) &iod, 0) >= 0) {
            remain = iod.piod_len;
#endif
            if (memchr(buf + read, '\0', remain)) {
                return buf;
            }

            read += remain;
        } else {
#if !PTBOX_FREEBSD
            perror("process_vm_readv");
#else
            perror("ptrace(PT_IO)");
#endif
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

bool pt_debugger::readbytes(unsigned long addr, char *buffer, size_t size) {
    if (use_peekdata)
        return readbytes_peekdata(addr, buffer, size);

#if !PTBOX_FREEBSD
    struct iovec local, remote;
    local.iov_base = (void *) buffer;
    local.iov_len = size;
    remote.iov_base = (void *) addr;
    remote.iov_len = size;

    if (process_vm_readv(tid, &local, 1, &remote, 1, 0) > 0)
        return true;

    perror("process_vm_readv");
#else
    struct ptrace_io_desc iod = {
        .piod_op = PIOD_READ_D,
        .piod_offs = (void *) addr,
        .piod_addr = (void *) buffer,
        .piod_len = size,
    };

    if (ptrace(PT_IO, tid, (caddr_t) &iod, 0) < 0)
        perror("ptrace(PT_IO)");
    else if (size == iod.piod_len)
        return true;
    else
        fprintf(stderr, "%d: failed to read %zu bytes, read %zu instead", tid, size, iod.piod_len);
#endif

    if (readbytes_peekdata(addr, buffer, size)) {
        use_peekdata = true;
        return true;
    }

    return false;
}

bool pt_debugger::readbytes_peekdata(unsigned long addr, char *buffer, size_t size) {
    union {
        ptrace_read_t val;
        char byte[sizeof(ptrace_read_t)];
    } data;
    size_t read = 0;

    while (read < size) {
        errno = 0;
#if PTBOX_FREEBSD
        data.val = ptrace(PT_READ_D, tid, (caddr_t) (addr + read), 0);
#else
        data.val = ptrace(PTRACE_PEEKDATA, tid, addr + read, NULL);
#endif
        if (data.val == -1 && errno)
            return false;
        memcpy(buffer + read, data.byte, size - read < sizeof(ptrace_read_t) ? size - read : sizeof(ptrace_read_t));
        read += sizeof(ptrace_read_t);
    }
    return true;
}
