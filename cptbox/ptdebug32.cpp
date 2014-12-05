#define _BSD_SOURCE
#include <sys/ptrace.h>
#include "ptbox.h"

#define EBX 0
#define ECX 1
#define EDX 2
#define ESI 3
#define EDI 4
#define EBP 5
#define EAX 6
#define DS 7
#define ES 8
#define FS 9
#define GS 10
#define ORIG_EAX 11
#define EIP 12
#define CS 13
#define EFL 14
#define UESP 15
#define SS 16

long pt_debugger32::peek_reg(int reg) {
    return ptrace(PTRACE_PEEKUSER, process->getpid(), 4 * reg, 0);
}

void pt_debugger32::poke_reg(int reg, long data) {
    ptrace(PTRACE_POKEUSER, process->getpid(), 4 * reg, data);
}

int pt_debugger32::syscall() {
    return (int) peek_reg(ORIG_EAX);
}

void pt_debugger32::syscall(int id) {
    poke_reg(ORIG_EAX, id);
}

#define make_arg(id, reg) \
    long pt_debugger32::arg##id() { \
        return peek_reg(reg); \
    } \
    \
    void pt_debugger32::arg##id(long data) {\
        poke_reg(reg, data); \
    }

make_arg(0, EBX);
make_arg(1, ECX);
make_arg(2, EDX);
make_arg(3, ESI);
make_arg(4, EDI);

#undef make_arg

long pt_debugger32::arg5() {
    return 0;
}

void pt_debugger32::arg5(long data) {}

bool pt_debugger32::is_exit(int syscall) {
    return syscall == 252 || syscall == 1;
}
