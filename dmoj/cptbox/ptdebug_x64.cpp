#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#if !PTBOX_FREEBSD && defined(__amd64__)
#include <asm/unistd.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>

int pt_debugger::native_abi = PTBOX_ABI_X64;

bool pt_debugger::supports_abi(int abi) {
    switch (abi) {
        case PTBOX_ABI_X86:
        case PTBOX_ABI_X64:
        case PTBOX_ABI_X32:
            return true;
    }
    return false;
}

uint32_t pt_debugger::seccomp_non_native_arch_list[] = { SCMP_ARCH_X86, SCMP_ARCH_X32, 0 };

int pt_debugger::abi_from_reg_size(size_t reg_size) {
    if (reg_size == sizeof regs.x86) {
        return PTBOX_ABI_X86;
    } else if (regs.x64.orig_rax & __X32_SYSCALL_BIT) {
        return PTBOX_ABI_X32;
    } else {
        return PTBOX_ABI_X64;
    }
}

size_t pt_debugger::reg_size_from_abi(int abi) {
    return abi_ == PTBOX_ABI_X86 ? sizeof regs.x86 : sizeof regs.x64;
}

#define UNKNOWN_ABI(source) fprintf(stderr, source ": Invalid ABI\n"), abort()

int pt_debugger::syscall() {
    switch (abi_) {
        case PTBOX_ABI_X86:
            return regs.x86.orig_eax;
        case PTBOX_ABI_X32:
            return regs.x64.orig_rax & ~__X32_SYSCALL_BIT;
        case PTBOX_ABI_X64:
            return regs.x64.orig_rax;
        case PTBOX_ABI_INVALID:
            return -1;
        default:
            UNKNOWN_ABI("ptdebug_x64.cpp:syscall getter");
    }
}

int pt_debugger::syscall(int id) {
    regs_changed = true;
    switch (abi_) {
        case PTBOX_ABI_X86:
            regs.x86.orig_eax = id;
            return 0;
        case PTBOX_ABI_X32:
            regs.x64.orig_rax = id | __X32_SYSCALL_BIT;
            return 0;
        case PTBOX_ABI_X64:
            regs.x64.orig_rax = id;
            return 0;
        case PTBOX_ABI_INVALID:
            return EINVAL;
        default:
            UNKNOWN_ABI("ptdebug_x64.cpp:syscall setter");
    }
}

#define MAKE_ACCESSOR(method, x86_name, x64_name)                                                                      \
    long pt_debugger::method() {                                                                                       \
        switch (abi_) {                                                                                                \
            case PTBOX_ABI_X86:                                                                                        \
                return regs.x86.x86_name;                                                                              \
            case PTBOX_ABI_X32:                                                                                        \
            case PTBOX_ABI_X64:                                                                                        \
                return regs.x64.x64_name;                                                                              \
            case PTBOX_ABI_INVALID:                                                                                    \
                return -1;                                                                                             \
            default:                                                                                                   \
                UNKNOWN_ABI("ptdebug_x64.cpp:" #method " getter");                                                     \
        }                                                                                                              \
    }                                                                                                                  \
                                                                                                                       \
    void pt_debugger::method(long value) {                                                                             \
        regs_changed = true;                                                                                           \
        switch (abi_) {                                                                                                \
            case PTBOX_ABI_X86:                                                                                        \
                regs.x86.x86_name = value;                                                                             \
                return;                                                                                                \
            case PTBOX_ABI_X32:                                                                                        \
            case PTBOX_ABI_X64:                                                                                        \
                regs.x64.x64_name = value;                                                                             \
                return;                                                                                                \
            case PTBOX_ABI_INVALID:                                                                                    \
                return;                                                                                                \
            default:                                                                                                   \
                UNKNOWN_ABI("ptdebug_x64.cpp:" #method " setter");                                                     \
        }                                                                                                              \
    }

MAKE_ACCESSOR(result, eax, rax)
MAKE_ACCESSOR(arg0, ebx, rdi)
MAKE_ACCESSOR(arg1, ecx, rsi)
MAKE_ACCESSOR(arg2, edx, rdx)
MAKE_ACCESSOR(arg3, esi, r10)
MAKE_ACCESSOR(arg4, edi, r8)
MAKE_ACCESSOR(arg5, ebp, r9)

#undef MAKE_ACCESSOR

bool pt_debugger::is_end_of_first_execve() {
    return syscall() == 59;
}
#endif /* __amd64__ */
