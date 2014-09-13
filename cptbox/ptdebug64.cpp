#define _BSD_SOURCE

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include "ptbox.h"

#define R15 0
#define R14 1
#define R13 2
#define R12 3
#define RBP 4
#define RBX 5
#define R11 6
#define R10 7
#define R9 8
#define R8 9
#define RAX 10
#define RCX 11
#define RDX 12
#define RSI 13
#define RDI 14
#define ORIG_RAX 15
#define RIP 16
#define CS 17
#define EFLAGS 18
#define RSP 19
#define SS 20
#define FS_BASE 21
#define GS_BASE 22
#define DS 23
#define ES 24
#define FS 25
#define GS 26

long pt_debugger64::peek_reg(int reg) {
    long res = ptrace(PTRACE_PEEKUSER, process->getpid(), 8 * reg, NULL);
    //if (res == -1)
    //    printf("%s: %d: error %d: %s\n", __FILE__, __LINE__, errno, strerror(errno));
    return res;
}

int pt_debugger64::syscall() {
    return (int) peek_reg(ORIG_RAX);
}

long pt_debugger64::arg0() {
    return peek_reg(RDI);
}

long pt_debugger64::arg1() {
    return peek_reg(RSI);
}

long pt_debugger64::arg2() {
    return peek_reg(RDX);
}

long pt_debugger64::arg3() {
    return peek_reg(R10);
}

long pt_debugger64::arg4() {
    return peek_reg(R8);
}

long pt_debugger64::arg5() {
    return peek_reg(R9);
}
