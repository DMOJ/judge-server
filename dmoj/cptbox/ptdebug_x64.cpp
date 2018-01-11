#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#ifdef HAS_DEBUGGER_X64
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>

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

int pt_debugger_x64::syscall() {
    return (int) peek_reg(ORIG_RAX);
}

void pt_debugger_x64::syscall(int id) {
#if PTBOX_FREEBSD
    poke_reg(RAX, id);
#else
    poke_reg(ORIG_RAX, id);
#endif
}

long pt_debugger_x64::result() {
    return peek_reg(RAX);
}

void pt_debugger_x64::result(long value) {
    poke_reg(RAX, value);
}

#define make_arg(id, reg) \
    long pt_debugger_x64::arg##id() { \
        return peek_reg(reg); \
    } \
    \
    void pt_debugger_x64::arg##id(long data) {\
        poke_reg(reg, data); \
    }

make_arg(0, RDI);
make_arg(1, RSI);
make_arg(2, RDX);
make_arg(3, R10);
make_arg(4, R8);
make_arg(5, R9);

#undef make_arg

bool pt_debugger_x64::is_exit(int syscall) {
#if defined(__FreeBSD__)
    return syscall == 1;
#else
    return syscall == 231 || syscall == 60;
#endif
}

int pt_debugger_x64::getpid_syscall() {
#if defined(__FreeBSD__)
    return 20;
#else
    return 39;
#endif
}

pt_debugger_x64::pt_debugger_x64() {
    execve_id = 59;
}
#endif /* HAS_DEBUGGER_X64 */
