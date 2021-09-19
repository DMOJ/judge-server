#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#ifdef __arm__
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

int pt_debugger::native_abi = PTBOX_ABI_ARM;

bool pt_debugger::supports_abi(int abi) {
    return abi == PTBOX_ABI_ARM;
}

uint32_t pt_debugger::seccomp_non_native_arch_list[] = { 0 };

int pt_debugger::abi_from_reg_size(size_t) {
    return PTBOX_ABI_ARM;
}

size_t pt_debugger::reg_size_from_abi(int) {
    return sizeof regs;
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

int pt_debugger::syscall(int id) {
    if (ptrace(PTRACE_SET_SYSCALL, tid, 0, id) == -1) {
        int err = errno;
        perror("ptrace(PTRACE_SET_SYSCALL)");
        return err;
    }
    return 0;
}

#define MAKE_ACCESSOR(method, reg_name)                                                                                \
    long pt_debugger::method() {                                                                                       \
        switch (abi_) {                                                                                                \
            case PTBOX_ABI_ARM:                                                                                        \
                return regs.reg_name;                                                                                  \
            case PTBOX_ABI_INVALID:                                                                                    \
                return -1;                                                                                             \
            default:                                                                                                   \
                UNKNOWN_ABI("ptdebug_arm.cpp:" #method " getter");                                                     \
        }                                                                                                              \
    }                                                                                                                  \
                                                                                                                       \
    void pt_debugger::method(long value) {                                                                             \
        regs_changed = true;                                                                                           \
        switch (abi_) {                                                                                                \
            case PTBOX_ABI_ARM:                                                                                        \
                regs.reg_name = value;                                                                                 \
            case PTBOX_ABI_INVALID:                                                                                    \
                return;                                                                                                \
            default:                                                                                                   \
                UNKNOWN_ABI("ptdebug_arm.cpp:" #method " setter");                                                     \
        }                                                                                                              \
    }

MAKE_ACCESSOR(result, ARM_r0)
MAKE_ACCESSOR(arg0, ARM_ORIG_r0)
MAKE_ACCESSOR(arg1, ARM_r1)
MAKE_ACCESSOR(arg2, ARM_r2)
MAKE_ACCESSOR(arg3, ARM_r3)
MAKE_ACCESSOR(arg4, ARM_r4)
MAKE_ACCESSOR(arg5, ARM_r5)

#undef MAKE_ACCESSOR

bool pt_debugger::is_end_of_first_execve() {
    return syscall() == 11;
}

#endif /* __arm__ */
