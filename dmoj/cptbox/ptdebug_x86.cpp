#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#ifdef HAS_DEBUGGER_X86
#include <sys/ptrace.h>

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

int pt_debugger_x86::syscall() {
    return (int) peek_reg(ORIG_EAX);
}

void pt_debugger_x86::syscall(int id) {
    poke_reg(ORIG_EAX, id);
}

long pt_debugger_x86::result() {
    return peek_reg(EAX);
}

void pt_debugger_x86::result(long value) {
    poke_reg(EAX, value);
}

#define make_arg(id, reg) \
    long pt_debugger_x86::arg##id() { \
        return peek_reg(reg); \
    } \
    \
    void pt_debugger_x86::arg##id(long data) {\
        poke_reg(reg, data); \
    }

make_arg(0, EBX);
make_arg(1, ECX);
make_arg(2, EDX);
make_arg(3, ESI);
make_arg(4, EDI);

#undef make_arg

long pt_debugger_x86::arg5() {
    return 0;
}

void pt_debugger_x86::arg5(long data) {}

bool pt_debugger_x86::is_exit(int syscall) {
    return syscall == 252 || syscall == 1;
}

int pt_debugger_x86::getpid_syscall() {
    return 20;
}

pt_debugger_x86::pt_debugger_x86() {
    execve_id = 11;
}
#endif /* HAS_DEBUGGER_X86 */
