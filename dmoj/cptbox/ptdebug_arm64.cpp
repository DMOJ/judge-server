#define _BSD_SOURCE
#include <sys/ptrace.h>
#include "ptbox.h"

#define ARM_x0 0
#define ARM_x1 1
#define ARM_x2 2
#define ARM_x3 3
#define ARM_x4 4
#define ARM_x5 5
#define ARM_x6 6
#define ARM_x7 7
#define ARM_x8 8
#define ARM_orig_x0
#define ARM_syscallno 35

int pt_debugger_arm64::syscall() {
    return (int) peek_reg(ARM_syscallno);
}

void pt_debugger_arm64::syscall(int id) {
    poke_reg(ARM_syscallno, id);
}

long pt_debugger_arm64::result() {
    return peek_reg(ARM_x0);
}

void pt_debugger_arm64::result(long value) {
    poke_reg(ARM_x0, value);
}

#define make_arg(id, reg) \
    long pt_debugger_arm64::arg##id() { \
        return peek_reg(reg); \
    } \
    \
    void pt_debugger_arm64::arg##id(long data) {\
        poke_reg(reg, data); \
    }

make_arg(0, ARM_ORIG_x0);
make_arg(1, ARM_x1);
make_arg(2, ARM_x2);
make_arg(3, ARM_x3);
make_arg(4, ARM_x4);
make_arg(5, ARM_x5);

#undef make_arg

bool pt_debugger_arm64::is_exit(int syscall) {
    return syscall == 93 || syscall == 94;
}

int pt_debugger_arm64::getpid_syscall() {
    return 172;
}

pt_debugger_arm64::pt_debugger_arm64() {
    execve_id = 221;
}
