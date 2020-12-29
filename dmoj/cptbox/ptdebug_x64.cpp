#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#if !PTBOX_FREEBSD && defined(__amd64__)
#include <asm/unistd.h>
#include <elf.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/uio.h>

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

#if PTBOX_SECCOMP
uint32_t pt_debugger::seccomp_non_native_arch_list[] = { SCMP_ARCH_X86, SCMP_ARCH_X32, 0 };
#endif

void pt_debugger::pre_syscall() {
    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = sizeof regs;
    if (ptrace(PTRACE_GETREGSET, tid, NT_PRSTATUS, &iovec)) {
        perror("ptrace(PTRACE_GETREGSET)");
        abi_ = PTBOX_ABI_INVALID;
    } else {
        if (iovec.iov_len == sizeof regs.x86) {
            abi_ = PTBOX_ABI_X86;
        } else if (regs.x64.orig_rax & __X32_SYSCALL_BIT) {
            abi_ = PTBOX_ABI_X32;
        } else {
            abi_ = PTBOX_ABI_X64;
        }
        regs_changed = false;
    }
}

void pt_debugger::post_syscall() {
    if (!regs_changed || abi_ == PTBOX_ABI_INVALID)
        return;

    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = abi_ == PTBOX_ABI_X86 ? sizeof regs.x86 : sizeof regs.x64;
    if (ptrace(PTRACE_SETREGSET, tid, NT_PRSTATUS, &iovec)) {
        perror("ptrace(PTRACE_SETREGSET)");
        abort();
    }
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

bool pt_debugger::syscall(int id) {
    regs_changed = true;
    switch (abi_) {
        case PTBOX_ABI_X86:
            regs.x86.orig_eax = id;
            return true;
        case PTBOX_ABI_X32:
            regs.x64.orig_rax = id | __X32_SYSCALL_BIT;
            return true;
        case PTBOX_ABI_X64:
            regs.x64.orig_rax = id;
            return true;
        case PTBOX_ABI_INVALID:
            return false;
        default:
            UNKNOWN_ABI("ptdebug_x64.cpp:syscall setter");
    }
}

#define MAKE_ACCESSOR(method, x86_name, x64_name) \
    long pt_debugger::method() { \
        switch (abi_) { \
            case PTBOX_ABI_X86: \
                return regs.x86.x86_name; \
            case PTBOX_ABI_X32: \
            case PTBOX_ABI_X64: \
                return regs.x64.x64_name; \
            case PTBOX_ABI_INVALID: \
                return -1; \
            default: \
                UNKNOWN_ABI("ptdebug_x64.cpp:" #method " getter"); \
        } \
    } \
    \
    void pt_debugger::method(long value) { \
        regs_changed = true; \
        switch (abi_) { \
            case PTBOX_ABI_X86: \
                regs.x86.x86_name = value; \
                return; \
            case PTBOX_ABI_X32: \
            case PTBOX_ABI_X64: \
                regs.x64.x64_name = value; \
                return; \
            case PTBOX_ABI_INVALID: \
                return; \
            default: \
                UNKNOWN_ABI("ptdebug_x64.cpp:" #method " setter"); \
        } \
    }

MAKE_ACCESSOR(result, eax, rax)
MAKE_ACCESSOR(arg0, ebx, rdi)
MAKE_ACCESSOR(arg1, ecx, rsi)
MAKE_ACCESSOR(arg2, edx, rdx)
MAKE_ACCESSOR(arg3, esi, r10)
MAKE_ACCESSOR(arg4, edi, r8)
MAKE_ACCESSOR(arg5, ebp, r9)

#undef MAKE_ACCESSOR

int pt_debugger::first_execve_syscall_id() {
    return 59;
}
#endif /* __amd64__ */
