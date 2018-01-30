#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#ifdef HAS_DEBUGGER_X86_ON_X64
#include <stdint.h>
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

long pt_debugger_x86_on_x64::peek_reg(int reg) {
    return (int32_t) pt_debugger::peek_reg(reg);
}

void pt_debugger_x86_on_x64::poke_reg(int reg, long data) {
    pt_debugger::poke_reg(reg, (int32_t) data);
}

int pt_debugger_x86_on_x64::syscall() {
    return (int) peek_reg(ORIG_RAX);
}

void pt_debugger_x86_on_x64::syscall(int id) {
    poke_reg(ORIG_RAX, id);
}

long pt_debugger_x86_on_x64::result() {
    return peek_reg(RAX);
}

void pt_debugger_x86_on_x64::result(long value) {
    poke_reg(RAX, value);
}

#define make_arg(id, reg) \
    long pt_debugger_x86_on_x64::arg##id() { \
        return peek_reg(reg); \
    } \
    \
    void pt_debugger_x86_on_x64::arg##id(long data) {\
        poke_reg(reg, data); \
    }

make_arg(0, RBX);
make_arg(1, RCX);
make_arg(2, RDX);
make_arg(3, RSI);
make_arg(4, RDI);

#undef make_arg

long pt_debugger_x86_on_x64::arg5() {
    return 0;
}

void pt_debugger_x86_on_x64::arg5(long data) {}

bool pt_debugger_x86_on_x64::is_exit(int syscall) {
    return syscall == 252 || syscall == 1;
}

int pt_debugger_x86_on_x64::getpid_syscall() {
    return 20;
}

pt_debugger_x86_on_x64::pt_debugger_x86_on_x64() {
    execve_id = 59;
}
#endif /* HAS_DEBUGGER_X86_ON_X64 */
