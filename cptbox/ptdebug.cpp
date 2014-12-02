#define _BSD_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/ptrace.h>
#include <unistd.h>
#include "ptbox.h"

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
    char *file;
    asprintf(&file, "/proc/%d/mem", process->getpid());
    memory = open(file, O_RDONLY);
    free(file);
}

char *pt_debugger::readstr(unsigned long addr) {
    unsigned long page = (addr + 4096) / 4096 * 4096 - addr;
    unsigned long size = 0;
    char *buf = (char *) malloc(page);

    lseek(memory, addr, SEEK_SET);
    while (true) {
        ssize_t done = read(memory, buf + size, page);
        if (!done) {
            buf[size?size-1:0] = '\0';
            break;
        }
        if (has_null(buf + size, done))
            break;
        size += done;
        page = (addr + size + 4096) / 4096 * 4096 - addr - size;
        buf = (char *) realloc(buf, size + page);
    }
    return buf;
}

void pt_debugger::freestr(char *buf) {
    free(buf);
}

pt_debugger::~pt_debugger() {
    if (memory)
        close(memory);
}
