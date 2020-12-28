#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#ifdef __arm__
#include <elf.h>
#include <sys/ptrace.h>
#include <sys/uio.h>

int pt_debugger::native_abi = PTBOX_ABI_ARM;

bool pt_debugger::supports_abi(int abi) {
    return abi == PTBOX_ABI_ARM;
}

#if PTBOX_SECCOMP
uint32_t pt_debugger::seccomp_non_native_arch_list[] = { 0 };
#endif

bool pt_debugger::pre_syscall() {
    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = sizeof regs;
    if (ptrace(PTRACE_GETREGSET, tid, NT_PRSTATUS, &iovec)) {
        perror("ptrace(PTRACE_GETREGSET)");
        abi_ = PTBOX_ABI_INVALID;
        return false;
    } else {
        abi_ = PTBOX_ABI_ARM;
        regs_changed = false;
        return true;
    }
}

bool pt_debugger::post_syscall() {
    if (!regs_changed || abi_ == PTBOX_ABI_INVALID)
        return true;

    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = sizeof regs;
    if (ptrace(PTRACE_SETREGSET, tid, NT_PRSTATUS, &iovec)) {
        perror("ptrace(PTRACE_SETREGSET)");
        return false;
    }
    return true;
}

#define UNKNOWN_ABI(source) fprintf(stderr, source ": Invalid ABI\n"), abort()

int pt_debugger::syscall() {
    switch (abi_) {
        case PTBOX_ABI_ARM:
            return regs.ARM_r7;
        case PTBOX_ABI_INVALID:
            return -1;
        default:
            UNKNOWN_ABI("ptdebug_arm.cpp:syscall getter");
    }
}

void pt_debugger::syscall(int id) {
    if (ptrace(PTRACE_SET_SYSCALL, tid, 0, id) == -1)
        perror("ptrace(PTRACE_SET_SYSCALL)");
}

#define MAKE_ACCESSOR(method, reg_name) \
    long pt_debugger::method() { \
        switch (abi_) { \
            case PTBOX_ABI_ARM: \
                return regs.reg_name; \
            case PTBOX_ABI_INVALID: \
                return -1; \
            default: \
                UNKNOWN_ABI("ptdebug_arm.cpp:" #method " getter"); \
        } \
    } \
    \
    void pt_debugger::method(long value) { \
        regs_changed = true; \
        switch (abi_) { \
            case PTBOX_ABI_ARM: \
                regs.reg_name = value; \
            case PTBOX_ABI_INVALID: \
                return; \
            default: \
                UNKNOWN_ABI("ptdebug_arm.cpp:" #method " setter"); \
        } \
    }

MAKE_ACCESSOR(result, ARM_r0)
MAKE_ACCESSOR(arg0, ARM_ORIG_r0)
MAKE_ACCESSOR(arg1, ARM_r1)
MAKE_ACCESSOR(arg2, ARM_r2)
MAKE_ACCESSOR(arg3, ARM_r3)
MAKE_ACCESSOR(arg4, ARM_r4)
MAKE_ACCESSOR(arg5, ARM_r5)

#undef MAKE_ACCESSOR

int pt_debugger::first_execve_syscall_id() {
    // There is no orig_r8 on ARM, and execve clears all registers.
    // Therefore, 0 is the register value when coming out of a system call.
    // We will pretend 0 is execve.
    return process->use_seccomp() ? 11 : 0;
}

#endif /* __arm__ */
