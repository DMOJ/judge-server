#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"
#include <cstdio>

#if defined(__arm64__) || defined(__aarch64__)
#include <elf.h>
#include <stdlib.h>
#include <sys/ptrace.h>
#include <sys/uio.h>

int pt_debugger::native_abi = PTBOX_ABI_ARM64;

bool pt_debugger::supports_abi(int abi) {
    switch (abi) {
        case PTBOX_ABI_ARM:
        case PTBOX_ABI_ARM64:
            return true;
    }
    return false;
}

#if PTBOX_SECCOMP
uint32_t pt_debugger::seccomp_non_native_arch_list[] = { SCMP_ARCH_ARM, 0 };
#endif

void pt_debugger::pre_syscall() {
    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = sizeof regs;
    if (ptrace(PTRACE_GETREGSET, tid, NT_PRSTATUS, &iovec)) {
        perror("ptrace(PTRACE_GETREGSET)");
        abi_ = PTBOX_ABI_INVALID;
    } else {
        abi_ = iovec.iov_len == sizeof regs.arm32 ? PTBOX_ABI_ARM : PTBOX_ABI_ARM64;
        regs_changed = false;
    }
}

void pt_debugger::post_syscall() {
    if (!regs_changed || abi_ == PTBOX_ABI_INVALID)
        return;

    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = abi_ == PTBOX_ABI_ARM ? sizeof regs.arm32 : sizeof regs.arm64;
    if (ptrace(PTRACE_SETREGSET, tid, NT_PRSTATUS, &iovec)) {
        perror("ptrace(PTRACE_SETREGSET)");
        abort();
    }
}

#define UNKNOWN_ABI(source) fprintf(stderr, source ": Invalid ABI\n"), abort()

int pt_debugger::syscall() {
    switch (abi_) {
        case PTBOX_ABI_ARM:
            return regs.arm32.r7;
        case PTBOX_ABI_ARM64:
            return regs.arm64.regs[8];
        case PTBOX_ABI_INVALID:
            return -1;
        default:
            UNKNOWN_ABI("ptdebug_arm64.cpp:syscall getter");
    }
}

void pt_debugger::syscall(int id) {
    struct iovec iovec;
    iovec.iov_base = &id;
    iovec.iov_len = sizeof id;

    if (ptrace(PTRACE_SETREGSET, tid, NT_ARM_SYSTEM_CALL, &iovec))
        perror("ptrace(PTRACE_SETREGSET, NT_ARM_SYSTEM_CALL)");
}

#define MAKE_ACCESSOR(method, arm32_name, arm64_name) \
    long pt_debugger::method() { \
        switch (abi_) { \
            case PTBOX_ABI_ARM: \
                return regs.arm32.arm32_name; \
            case PTBOX_ABI_ARM64: \
                return regs.arm64.arm64_name; \
            case PTBOX_ABI_INVALID: \
                return -1; \
            default: \
                UNKNOWN_ABI("ptdebug_arm64.cpp:" #method " getter"); \
        } \
    } \
    \
    void pt_debugger::method(long value) { \
        regs_changed = true; \
        switch (abi_) { \
            case PTBOX_ABI_ARM: \
                regs.arm32.arm32_name = value; \
                return; \
            case PTBOX_ABI_ARM64: \
                regs.arm64.arm64_name = value; \
                return; \
            case PTBOX_ABI_INVALID: \
                return; \
            default: \
                UNKNOWN_ABI("ptdebug_arm64.cpp:" #method " setter"); \
        } \
    }

MAKE_ACCESSOR(result, r7, regs[8])
MAKE_ACCESSOR(arg0, r0, regs[0])
MAKE_ACCESSOR(arg1, r1, regs[1])
MAKE_ACCESSOR(arg2, r2, regs[2])
MAKE_ACCESSOR(arg3, r3, regs[3])
MAKE_ACCESSOR(arg4, r4, regs[4])
MAKE_ACCESSOR(arg5, r5, regs[5])

#undef MAKE_ACCESSOR

int pt_debugger::first_execve_syscall_id() {
    // There is no orig_x8 on ARM64, and execve clears all registers.
    // Therefore, 0 is the register value when coming out of a system call.
    // We will pretend 0 is execve if we aren't using seccomp.
    return process->use_seccomp() ? 221 : 0;
}
#endif /* defined(__arm64__) || defined(__aarch64__) */
