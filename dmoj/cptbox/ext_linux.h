#include <sys/ptrace.h>

inline long ptrace_traceme() {
    return ptrace(PTRACE_TRACEME, 0, NULL, NULL);
}