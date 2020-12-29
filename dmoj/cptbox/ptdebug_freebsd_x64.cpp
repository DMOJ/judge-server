#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#if PTBOX_FREEBSD && defined(__amd64__)
#include <stdio.h>
#include <stdlib.h>

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

bool pt_debugger::syscall(int value) {
    regs_changed = true;
    switch (abi_) {
        case PTBOX_ABI_FREEBSD_X64:
            regs.r_rax = value;
            return true; \
        case PTBOX_ABI_INVALID:
            return false;
        default: \
            UNKNOWN_ABI("ptdebug_freebsd_x64.cpp:syscall setter");
    }
}

#define MAKE_ACCESSOR(method, reg_name) \
    long pt_debugger::method() { \
        switch (abi_) { \
            case PTBOX_ABI_FREEBSD_X64: \
                return regs.r_##reg_name; \
            case PTBOX_ABI_INVALID: \
                return -1; \
            default: \
                UNKNOWN_ABI("ptdebug_freebsd_x64.cpp:" #method " getter"); \
        } \
    } \
    \
    void pt_debugger::method(long value) { \
        regs_changed = true; \
        switch (abi_) { \
            case PTBOX_ABI_FREEBSD_X64: \
                regs.r_##reg_name = value; \
                return; \
            case PTBOX_ABI_INVALID: \
                return; \
            default: \
                UNKNOWN_ABI("ptdebug_freebsd_x64.cpp:" #method " setter"); \
        } \
    }

MAKE_ACCESSOR(result, rax)
MAKE_ACCESSOR(arg0, rdi)
MAKE_ACCESSOR(arg1, rsi)
MAKE_ACCESSOR(arg2, rdx)
MAKE_ACCESSOR(arg3, r10)
MAKE_ACCESSOR(arg4, r8)
MAKE_ACCESSOR(arg5, r9)

#undef MAKE_ACCESSOR

int pt_debugger::first_execve_syscall_id() {
    return 59;
}
#endif /* __amd64__ */
