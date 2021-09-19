#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#ifdef __i386__
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

int pt_debugger::native_abi = PTBOX_ABI_X86;

bool pt_debugger::supports_abi(int abi) {
    return abi == PTBOX_ABI_X86;
}

uint32_t pt_debugger::seccomp_non_native_arch_list[] = { 0 };

int pt_debugger::abi_from_reg_size(size_t) {
    return PTBOX_ABI_X86;
}

size_t pt_debugger::reg_size_from_abi(int) {
    return sizeof regs;
}

#define UNKNOWN_ABI(source) fprintf(stderr, source ": Invalid ABI\n"), abort()

int pt_debugger::syscall() {
    switch (abi_) {
        case PTBOX_ABI_X86:
            return regs.orig_eax;
        case PTBOX_ABI_INVALID:
            return -1;
        default:
            UNKNOWN_ABI("ptdebug_x86.cpp:syscall getter");
    }
}

int pt_debugger::syscall(int id) {
    regs_changed = true;
    switch (abi_) {
        case PTBOX_ABI_X86:
            regs.orig_eax = id;
            return 0;
        case PTBOX_ABI_INVALID:
            return EINVAL;
        default:
            UNKNOWN_ABI("ptdebug_x86.cpp:syscall setter");
    }
}

#define MAKE_ACCESSOR(method, reg_name)                                                                                \
    long pt_debugger::method() {                                                                                       \
        switch (abi_) {                                                                                                \
            case PTBOX_ABI_X86:                                                                                        \
                return regs.reg_name;                                                                                  \
            case PTBOX_ABI_INVALID:                                                                                    \
                return -1;                                                                                             \
            default:                                                                                                   \
                UNKNOWN_ABI("ptdebug_x86.cpp:" #method " getter");                                                     \
        }                                                                                                              \
    }                                                                                                                  \
                                                                                                                       \
    void pt_debugger::method(long value) {                                                                             \
        regs_changed = true;                                                                                           \
        switch (abi_) {                                                                                                \
            case PTBOX_ABI_X86:                                                                                        \
                regs.reg_name = value;                                                                                 \
            case PTBOX_ABI_INVALID:                                                                                    \
                return;                                                                                                \
            default:                                                                                                   \
                UNKNOWN_ABI("ptdebug_x86.cpp:" #method " setter");                                                     \
        }                                                                                                              \
    }

MAKE_ACCESSOR(result, eax)
MAKE_ACCESSOR(arg0, ebx)
MAKE_ACCESSOR(arg1, ecx)
MAKE_ACCESSOR(arg2, edx)
MAKE_ACCESSOR(arg3, esi)
MAKE_ACCESSOR(arg4, edi)
#undef MAKE_ACCESSOR

long pt_debugger::arg5() {
    return 0;
}

void pt_debugger::arg5(long data) {}

bool pt_debugger::is_end_of_first_execve() {
    return syscall() == 11;
}
#endif /* __i386__ */
