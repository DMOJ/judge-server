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
        data.val = ptrace(PTRACE_PEEKDATA, process->getpid(), addr + read, NULL);
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