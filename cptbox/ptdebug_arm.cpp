#define _BSD_SOURCE
#include <sys/ptrace.h>
#include "ptbox.h"

#define ARM_cpsr 16
#define ARM_pc 15
#define ARM_lr 14
#define ARM_sp 13
#define ARM_ip 12
#define ARM_fp 11
#define ARM_r10 10
#define ARM_r9 9
#define ARM_r8 8
#define ARM_r7 7
#define ARM_r6 6
#define ARM_r5 5
#define ARM_r4 4
#define ARM_r3 3
#define ARM_r2 2
#define ARM_r1 1
#define ARM_r0 0
#define ARM_ORIG_r0 17

long pt_debugger_arm::peek_reg(int reg) {
    return ptrace(PTRACE_PEEKUSER, process->getpid(), 4 * reg, 0);
}

void pt_debugger_arm::poke_reg(int reg, long data) {
    ptrace(PTRACE_POKEUSER, process->getpid(), 4 * reg, data);
}

int pt_debugger_arm::syscall() {
    return (int) peek_reg(ARM_r7);
}

void pt_debugger_arm::syscall(int id) {
    poke_reg(ARM_r7, id);
}

long pt_debugger_arm::result() {
    return peek_reg(ARM_r0);
}

void pt_debugger_arm::result(long value) {
    poke_reg(ARM_r0, value);
}

#define make_arg(id, reg) \
    long pt_debugger_arm::arg##id() { \
        return peek_reg(reg); \
    } \
    \
    void pt_debugger_arm::arg##id(long data) {\
        poke_reg(reg, data); \
    }

make_arg(0, ARM_ORIG_r0);
make_arg(1, ARM_r1);
make_arg(2, ARM_r2);
make_arg(3, ARM_r3);
make_arg(4, ARM_r4);
make_arg(5, ARM_r5);

#undef make_arg

bool pt_debugger_arm::is_exit(int syscall) {
    return syscall == 248 || syscall == 1;
}

int pt_debugger_arm::getpid_syscall() {
    return 20;
}

pt_debugger_arm::pt_debugger_arm() {
    execve_id = 11;
}
