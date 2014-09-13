#define _BSD_SOURCE
#include <sys/ptrace.h>
#include "ptbox.h"

#define EBX 0
#define ECX 1
#define EDX 2
#define ESI 3
#define EDI 4
#define EBP 5
#define EAX 6
#define DS 7
#define ES 8
#define FS 9
#define GS 10
#define ORIG_EAX 11
#define EIP 12
#define CS 13
#define EFL 14
#define UESP 15
#define SS 16

long pt_debugger32::peek_reg(int reg) {
    return ptrace(PTRACE_PEEKUSER, process->getpid(), 4 * reg, 0);
}

int pt_debugger32::syscall() {
    return (int) peek_reg(ORIG_EAX);
}

long pt_debugger32::arg0() {
    return peek_reg(EBX);
}

long pt_debugger32::arg1() {
    return peek_reg(ECX);
}

long pt_debugger32::arg2() {
    return peek_reg(EDX);
}

long pt_debugger32::arg3() {
    return peek_reg(ESI);
}

long pt_debugger32::arg4() {
    return peek_reg(EDI);
}

long pt_debugger32::arg5() {
    return 0;
}
