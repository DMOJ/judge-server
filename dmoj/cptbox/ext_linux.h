#include <sys/ptrace.h>

inline long ptrace_traceme() {
    return ptrace(PTRACE_TRACEME, 0, NULL, NULL);
}

inline long get_reg(pt_debugger *debugger, int reg) {
    return ptrace(PTRACE_PEEKUSER, debugger->tid, sizeof(long) * reg, 0);
}

inline void set_reg(pt_debugger *debugger, int reg, long data) {
    ptrace(PTRACE_POKEUSER, debugger->tid, sizeof(long) * reg, data);
}