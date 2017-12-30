#define _BSD_SOURCE
#include <sys/ptrace.h>
#include <sys/uio.h>
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

#ifdef PTBOX_NEED_PRE_POST_SYSCALL
#include <elf.h>

void pt_debugger_arm_on_arm64::pre_syscall() {
    struct iovec iovec;
    iovec.iov_base = arm_reg;
    iovec.iov_len = sizeof arm_reg;
    if (ptrace(PTRACE_GETREGSET, tid, NT_PRSTATUS, &iovec))
        perror("ptrace(PTRACE_GETREGSET)");

    arm64_reg_changed = false;
}

void pt_debugger_arm_on_arm64::post_syscall() {
    if (!arm64_reg_changed)
        return;

    struct iovec iovec;
    iovec.iov_base = arm_reg;
    iovec.iov_len = sizeof arm_reg;
    if (ptrace(PTRACE_SETREGSET, tid, NT_PRSTATUS, &iovec))
        perror("ptrace(PTRACE_SETREGSET)");
}
#endif

long pt_debugger_arm_on_arm64::peek_reg(int reg) {
    return arm_reg[reg];
}

void pt_debugger_arm_on_arm64::poke_reg(int reg, long data) {
    arm_reg[reg] = (uint32_t) data;
    arm64_reg_changed = true;
}

int pt_debugger_arm_on_arm64::syscall() {
    return (int) peek_reg(ARM_r7);
}

long pt_debugger_arm_on_arm64::result() {
    return peek_reg(ARM_r0);
}

void pt_debugger_arm_on_arm64::result(long value) {
    poke_reg(ARM_r0, value);
}

#define make_arg(id, reg) \
    long pt_debugger_arm_on_arm64::arg##id() { \
        return peek_reg(reg); \
    } \
    \
    void pt_debugger_arm_on_arm64::arg##id(long data) {\
        poke_reg(reg, data); \
    }

make_arg(0, ARM_ORIG_r0);
make_arg(1, ARM_r1);
make_arg(2, ARM_r2);
make_arg(3, ARM_r3);
make_arg(4, ARM_r4);
make_arg(5, ARM_r5);

#undef make_arg

bool pt_debugger_arm_on_arm64::is_exit(int syscall) {
    return syscall == 248 || syscall == 1;
}

int pt_debugger_arm_on_arm64::getpid_syscall() {
    return 20;
}

pt_debugger_arm_on_arm64::pt_debugger_arm_on_arm64() {
    // execve is actually 221, but...
    // There is no orig_x8 on ARM, and execve clears all registers.
    // Therefore, 0 is the register value when coming out of a system call.
    // We will pretend 0 is execve.
    execve_id = 0;
}
