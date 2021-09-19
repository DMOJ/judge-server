#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#if PTBOX_FREEBSD && defined(__amd64__)
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

#define CARRY_FLAG 1

int pt_debugger::native_abi = PTBOX_ABI_FREEBSD_X64;

bool pt_debugger::supports_abi(int abi) {
    return abi == PTBOX_ABI_FREEBSD_X64;
}

int pt_debugger::abi_from_reg_size(size_t) {
    return PTBOX_ABI_FREEBSD_X64;
}

#define UNKNOWN_ABI(source) fprintf(stderr, source ": Invalid ABI\n"), abort()

int pt_debugger::syscall() {
    return _bsd_syscall;
}

int pt_debugger::syscall(int id) {
    regs_changed = true;
    switch (abi_) {
        case PTBOX_ABI_FREEBSD_X64:
            regs.r_rax = id;
            return 0;
        case PTBOX_ABI_INVALID:
            return EINVAL;
        default:
            UNKNOWN_ABI("ptdebug_freebsd_x64.cpp:syscall setter");
    }
}

long pt_debugger::result() {
    switch (abi_) {
        case PTBOX_ABI_FREEBSD_X64:
            return regs.r_rflags & CARRY_FLAG ? -1 : regs.r_rax;
        case PTBOX_ABI_INVALID:
            return -1;
        default:
            UNKNOWN_ABI("ptdebug_freebsd_x64.cpp: result getter");
    }
}

void pt_debugger::result(long value) {
    regs_changed = true;
    switch (abi_) {
        case PTBOX_ABI_FREEBSD_X64:
            regs.r_rax = value;
            regs.r_rflags &= ~CARRY_FLAG;
            return;
        case PTBOX_ABI_INVALID:
            return;
        default:
            UNKNOWN_ABI("ptdebug_freebsd_x64.cpp: result setter");
    }
}

long pt_debugger::error() {
    switch (abi_) {
        case PTBOX_ABI_FREEBSD_X64:
            return regs.r_rflags & CARRY_FLAG ? regs.r_rax : 0;
        case PTBOX_ABI_INVALID:
            return -1;
        default:
            UNKNOWN_ABI("ptdebug_freebsd_x64.cpp: error getter");
    }
}

void pt_debugger::error(long value) {
    regs_changed = true;
    switch (abi_) {
        case PTBOX_ABI_FREEBSD_X64:
            regs.r_rax = value;
            regs.r_rflags |= CARRY_FLAG;
            return;
        case PTBOX_ABI_INVALID:
            return;
        default:
            UNKNOWN_ABI("ptdebug_freebsd_x64.cpp: error setter");
    }
}

#define MAKE_ACCESSOR(method, reg_name)                                                                                \
    long pt_debugger::method() {                                                                                       \
        switch (abi_) {                                                                                                \
            case PTBOX_ABI_FREEBSD_X64:                                                                                \
                return regs.r_##reg_name;                                                                              \
            case PTBOX_ABI_INVALID:                                                                                    \
                return -1;                                                                                             \
            default:                                                                                                   \
                UNKNOWN_ABI("ptdebug_freebsd_x64.cpp:" #method " getter");                                             \
        }                                                                                                              \
    }                                                                                                                  \
                                                                                                                       \
    void pt_debugger::method(long value) {                                                                             \
        regs_changed = true;                                                                                           \
        switch (abi_) {                                                                                                \
            case PTBOX_ABI_FREEBSD_X64:                                                                                \
                regs.r_##reg_name = value;                                                                             \
                return;                                                                                                \
            case PTBOX_ABI_INVALID:                                                                                    \
                return;                                                                                                \
            default:                                                                                                   \
                UNKNOWN_ABI("ptdebug_freebsd_x64.cpp:" #method " setter");                                             \
        }                                                                                                              \
    }

MAKE_ACCESSOR(arg0, rdi)
MAKE_ACCESSOR(arg1, rsi)
MAKE_ACCESSOR(arg2, rdx)
MAKE_ACCESSOR(arg3, r10)
MAKE_ACCESSOR(arg4, r8)
MAKE_ACCESSOR(arg5, r9)

#undef MAKE_ACCESSOR

bool pt_debugger::is_end_of_first_execve() {
    return !is_enter() && syscall() == 59 && result() == 0;
}
#endif /* __amd64__ */
