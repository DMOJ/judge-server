#define _DEFAULT_SOURCE
#define _BSD_SOURCE
#include "ptbox.h"

#ifdef __i386__
#include <elf.h>
#include <sys/ptrace.h>
#include <sys/uio.h>

bool pt_debugger::supports_abi(int abi) {
    return abi == PTBOX_ABI_X86;
}

void pt_debugger::pre_syscall() {
    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = sizeof regs;
    if (ptrace(PTRACE_GETREGSET, tid, NT_PRSTATUS, &iovec)) {
        perror("ptrace(PTRACE_GETREGSET)");
        abi_ = PTBOX_ABI_INVALID;
    } else {
        abi_ = PTBOX_ABI_X86;
        regs_changed = false;
    }
}

void pt_debugger::post_syscall() {
    if (!regs_changed || abi_ == PTBOX_ABI_INVALID)
        return;

    struct iovec iovec;
    iovec.iov_base = &regs;
    iovec.iov_len = sizeof regs;
    if (ptrace(PTRACE_SETREGSET, tid, NT_PRSTATUS, &iovec)) {
        perror("ptrace(PTRACE_SETREGSET)");
    }
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

void pt_debugger::syscall(int id) {
    regs_changed = true;
    switch (abi_) {
        case PTBOX_ABI_X86:
            regs.orig_eax = id;
            return;
        case PTBOX_ABI_INVALID:
            return;
        default:
            UNKNOWN_ABI("ptdebug_x86.cpp:syscall setter");
    }
}

#define MAKE_ACCESSOR(method, reg_name) \
    long pt_debugger::method() { \
        switch (abi_) { \
            case PTBOX_ABI_X86: \
                return regs.reg_name; \
            case PTBOX_ABI_INVALID: \
                return -1; \
            default: \
                UNKNOWN_ABI("ptdebug_x86.cpp:" #method " getter"); \
        } \
    } \
    \
    void pt_debugger::method(long value) { \
        regs_changed = true; \
        switch (abi_) { \
            case PTBOX_ABI_X86: \
                regs.reg_name = value; \
            case PTBOX_ABI_INVALID: \
                return; \
            default: \
                UNKNOWN_ABI("ptdebug_x86.cpp:" #method " setter"); \
        } \
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

int pt_debugger::first_execve_syscall_id() {
    return 11;
}
#endif /* __i386__ */
