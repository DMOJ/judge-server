#include <sys/ptrace.h>
#include <sys/types.h>

inline long ptrace_traceme() {
    return ptrace(PT_TRACE_ME, 0, NULL, 0);
}

// Debian GNU/kFreeBSD neglected to define this in their libc.
#if defined(__FreeBSD_kernel__) && !defined(PT_FOLLOW_FORK)
#define PT_FOLLOW_FORK 23
#endif

// Constant for wait4
#define __WALL 0
