#define _BSD_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/ptrace.h>
#include <unistd.h>
#include "ptbox.h"

pt_debugger::pt_debugger() : on_return_callback(NULL) {}

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

void pt_debugger::new_process() {}

void pt_debugger::settid(pid_t tid) {
    this->tid = tid;
#if defined(__FreeBSD__)
    struct reg bsd_regs;
    ptrace(PT_GETREGS, tid, (caddr_t) &bsd_regs, 0);
    map_regs_to_linux(&bsd_regs, &bsd_converted_regs);
#endif
}

long pt_debugger::peek_reg(int idx) {
#if defined(__FreeBSD__)
    return ((reg_type*)&bsd_converted_regs)[idx];
#else
    return ptrace(PTRACE_PEEKUSER, tid, sizeof(long) * idx, 0);
#endif
}

void pt_debugger::poke_reg(int idx, long data) {
#if defined(__FreeBSD__)
    ((reg_type*)&bsd_converted_regs)[idx] = data;

    struct reg bsd_regs;
    map_regs_from_linux(&bsd_regs, &bsd_converted_regs);
    ptrace(PT_SETREGS, tid, (caddr_t) &bsd_regs, 0);
#else
    ptrace(PTRACE_POKEUSER, tid, sizeof(long) * idx, data);
#endif
}

char *pt_debugger::readstr(unsigned long addr, size_t max_size) {
    size_t size = 4096, read = 0;
    char *buf = (char *) malloc(size);
    union {
        long val;
        char byte[sizeof(long)];
    } data;

    while (true) {
        if (read + sizeof(long) > size) {
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
#if defined(__FreeBSD__)
        // TODO: we could use PT_IO to speed up this entire function by reading chunks rather than byte
        data.val = ptrace(PT_READ_D, tid, (caddr_t) (addr + read), 0);
#else
        data.val = ptrace(PTRACE_PEEKDATA, tid, addr + read, NULL);
#endif
        memcpy(buf + read, data.byte, sizeof(long));
        if (has_null(data.byte, sizeof(long)))
            break;
        read += sizeof(long);
    }
    return buf;
}

void pt_debugger::freestr(char *buf) {
    free(buf);
}

pt_debugger::~pt_debugger() {}
