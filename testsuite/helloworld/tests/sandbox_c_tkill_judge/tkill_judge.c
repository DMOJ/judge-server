#define _DEFAULT_SOURCE
#include <errno.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

// The sandbox rewrites tkill(tid, sig) into tgkill(pid, tid, sig) and restores the arguments on return. Check that
// they come back unchanged, using a third argument that tkill ignores but that becomes sig after the rewrite.
static int tkill_self_clobbers_args(long tid) {
#if defined(__x86_64__)
    register long rax __asm__("rax") = SYS_tkill;
    register long rdi __asm__("rdi") = tid;
    register long rsi __asm__("rsi") = 0;
    register long rdx __asm__("rdx") = 0x1234;
    __asm__ volatile("syscall" : "+r"(rax), "+r"(rdi), "+r"(rsi), "+r"(rdx) : : "rcx", "r11", "memory");
    return rax != 0 || rdi != tid || rsi != 0 || rdx != 0x1234;
#elif defined(__aarch64__)
    register long x8 __asm__("x8") = SYS_tkill;
    register long x0 __asm__("x0") = tid;  // Also receives the result.
    register long x1 __asm__("x1") = 0;
    register long x2 __asm__("x2") = 0x1234;
    __asm__ volatile("svc #0" : "+r"(x0), "+r"(x1), "+r"(x2) : "r"(x8) : "memory");
    return x0 != 0 || x1 != 0 || x2 != 0x1234;
#else
    return syscall(SYS_tkill, tid, 0) != 0;
#endif
}

int main() {
    // A sandbox denial would be EPERM; ESRCH means the kernel refused it as tgkill.
    if (syscall(SYS_tkill, getppid(), 0) == 0) {
        puts("Signalled the judge");
    } else if (errno != ESRCH) {
        printf("Wrong errno: %d", errno);
    } else if (tkill_self_clobbers_args(syscall(SYS_gettid))) {
        puts("tkill on ourselves failed or clobbered its arguments");
    } else {
        puts("Hello, World!");
    }
}
