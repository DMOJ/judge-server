#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"
#include <cstdio>

#ifdef HAS_DEBUGGER_ARM
#include <sys/ptrace.h>
#include <sys/uio.h>
#include <unistd.h>

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

#include <elf.h>

void pt_debugger_arm::pre_syscall() {
    struct iovec iovec;
    iovec.iov_base = arm32_reg;
    iovec.iov_len = sizeof arm32_reg;
    if (ptrace(PTRACE_GETREGSET, tid, NT_PRSTATUS, &iovec))
        perror("ptrace(PTRACE_GETREGSET)");

    arm_reg_changed = false;
}

void pt_debugger_arm::post_syscall() {
    if (!arm_reg_changed)
        return;

    struct iovec iovec;
    iovec.iov_base = arm32_reg;
    iovec.iov_len = sizeof arm32_reg;
    if (ptrace(PTRACE_SETREGSET, tid, NT_PRSTATUS, &iovec))
        perror("ptrace(PTRACE_SETREGSET)");
}

long pt_debugger_arm::peek_reg(int reg) {
    return arm32_reg[reg];
}

// Note that this deliberately doesn't update arm64_reg.
// The kernel only updates x0 on a system call, so x8 must not be changed.
void pt_debugger_arm::syscall(int id) {
#if defined(__aarch64__) || defined(__arm64__)
// Even if we are debugging ARM on ARM64, we must still use NT_ARM_SYSTEM_CALL.
#ifndef NT_ARM_SYSTEM_CALL
#define NT_ARM_SYSTEM_CALL 0x404
#endif
    struct iovec iovec;
    iovec.iov_base = &id;
    iovec.iov_len = sizeof id;

    if (ptrace(PTRACE_SETREGSET, tid, NT_ARM_SYSTEM_CALL, &iovec))
        perror("ptrace(PTRACE_SETREGSET, NT_ARM_SYSTEM_CALL)");
#else
#ifndef SYS_ptrace
#define SYS_ptrace 26
#endif
#ifndef PTRACE_SET_SYSCALL
#define PTRACE_SET_SYSCALL 23
#endif
    if (::syscall(SYS_ptrace, PTRACE_SET_SYSCALL, tid, 0, id) == -1)
        perror("ptrace(PTRACE_SET_SYSCALL");
#endif
}

void pt_debugger_arm::poke_reg(int reg, long data) {
    arm32_reg[reg] = (uint32_t) data;
    arm_reg_changed = true;
}

int pt_debugger_arm::syscall() {
    return (int) peek_reg(ARM_r7);
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
    // execve is actually 11, but...
    // There is no orig_r8 on ARM, and execve clears all registers.
    // Therefore, 0 is the register value when coming out of a system call.
    // We will pretend 0 is execve.
    execve_id = 0;
}
#endif /* HAS_DEBUGGER_ARM */
