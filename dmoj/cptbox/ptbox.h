#pragma once
#ifndef idA6398CB6_D711_4634_9D89FF6B1D215169
#define idA6398CB6_D711_4634_9D89FF6B1D215169

#include <stddef.h>
#include <inttypes.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/param.h>

#include <sys/ptrace.h>

#include <map>

#if defined(__FreeBSD__) || defined(__FreeBSD_kernel__)
#   define PTBOX_FREEBSD 1
#else
#   define PTBOX_FREEBSD 0
#endif

#ifndef PTBOX_NO_SECCOMP
#define PTBOX_SECCOMP !PTBOX_FREEBSD
#else
#define PTBOX_SECCOMP 0
#endif

#if PTBOX_SECCOMP
#include <seccomp.h>
#endif

#if PTBOX_FREEBSD
#include "ext_freebsd.h"
#else
#include "ext_linux.h"
#include <sys/user.h>
#endif

#define MAX_SYSCALL 568
#define PTBOX_HANDLER_DENY 0
#define PTBOX_HANDLER_ALLOW 1
#define PTBOX_HANDLER_CALLBACK 2
#define PTBOX_HANDLER_STDOUTERR 3

#define PTBOX_EVENT_ATTACH 0
#define PTBOX_EVENT_EXITING 1
#define PTBOX_EVENT_EXITED 2
#define PTBOX_EVENT_SIGNAL 3
#define PTBOX_EVENT_PROTECTION 4

#define PTBOX_EXIT_NORMAL 0
#define PTBOX_EXIT_PROTECTION 1
#define PTBOX_EXIT_SEGFAULT 2

enum {
    PTBOX_ABI_X86 = 0,
    PTBOX_ABI_X64,
    PTBOX_ABI_X32,
    PTBOX_ABI_ARM,
    PTBOX_ABI_ARM64,
    PTBOX_ABI_COUNT,
};

#if !PTBOX_FREEBSD && defined(__amd64__)
#   include "ptdebug_x64.h"
#endif

inline void timespec_add(struct timespec *a, struct timespec *b, struct timespec *result) {
    result->tv_sec = a->tv_sec + b->tv_sec ;
    result->tv_nsec = a->tv_nsec + b->tv_nsec ;
    if (result->tv_nsec >= 1000000000L) {
        result->tv_sec++;
        result->tv_nsec = result->tv_nsec - 1000000000L ;
    }
}

inline void timespec_sub(struct timespec *a, struct timespec *b, struct timespec *result) {
    if ((a->tv_sec < b->tv_sec) ||
        ((a->tv_sec == b->tv_sec) &&
         (a->tv_nsec <= b->tv_nsec))) { /* a <= b? */
        result->tv_sec = result->tv_nsec = 0 ;
    } else { /* a > b */
        result->tv_sec = a->tv_sec - b->tv_sec;
        if (a->tv_nsec < b->tv_nsec) {
            result->tv_nsec = a->tv_nsec + 1000000000L - b->tv_nsec ;
            result->tv_sec--; /* Borrow a second-> */
        } else {
            result->tv_nsec = a->tv_nsec - b->tv_nsec ;
        }
    }
}

class pt_debugger;

typedef int (*pt_handler_callback)(void *context, int syscall);
typedef void (*pt_syscall_return_callback)(void *context, int syscall);
typedef int (*pt_fork_handler)(void *context);
typedef int (*pt_event_callback)(void *context, int event, unsigned long param);

class pt_process {
public:
    pt_process(pt_debugger *debugger);
    void set_callback(pt_handler_callback, void *context);
    void set_event_proc(pt_event_callback, void *context);
    int set_handler(int abi, int syscall, int handler);
    bool trace_syscalls() { return _trace_syscalls; }
    void trace_syscalls(bool value) { _trace_syscalls = value; }
    int spawn(pt_fork_handler child, void *context);
    int monitor();
    int getpid() { return pid; }
    double execution_time() { return exec_time.tv_sec + exec_time.tv_nsec / 1000000000.0; }
    double wall_clock_time();
    const rusage *getrusage() { return &_rusage; }
    bool was_initialized() { return _initialized; }
protected:
    int dispatch(int event, unsigned long param);
    int protection_fault(int syscall);
private:
    pid_t pid;
    int handler[PTBOX_ABI_COUNT][MAX_SYSCALL];
    pt_handler_callback callback;
    void *context;
    struct timespec exec_time, start_time, end_time;
    struct rusage _rusage;
    pt_debugger *debugger;
    pt_event_callback event_proc;
    void *event_context;
    bool _trace_syscalls;
    bool _initialized;
};

class pt_debugger {
public:
    pt_debugger();

    int syscall();
    void syscall(int);
    long result();
    void result(long);
    long arg0();
    long arg1();
    long arg2();
    long arg3();
    long arg4();
    long arg5();
    void arg0(long);
    void arg1(long);
    void arg2(long);
    void arg3(long);
    void arg4(long);
    void arg5(long);

    long peek_reg(int reg);
    void poke_reg(int reg, long data);

    bool is_exit(int syscall);
    int getpid_syscall();
    int execve_syscall();

    void set_process(pt_process *);
    virtual void new_process();
    virtual char *readstr(unsigned long addr, size_t max_size);
    virtual void freestr(char *);
    virtual ~pt_debugger();

    pid_t gettid() { return tid; }
    pid_t tid; // TODO maybe call super instead
    pid_t getpid() { return process->getpid(); }

#if PTBOX_FREEBSD
    void update_syscall(struct ptrace_lwpinfo *info);
    void setpid(pid_t pid);
#else
    void settid(pid_t tid);
    bool is_enter() {
      // All seccomp events are enter events.
      return PTBOX_SECCOMP ? true : syscall_[tid] != 0;
    }
#endif

    void pre_syscall();
    void post_syscall();
    int abi() { return abi_; }
    static bool supports_abi(int);

    void on_return(pt_syscall_return_callback callback, void *context) {
        on_return_callback = callback;
        on_return_context = context;
    }
private:
    pt_process *process;
    pt_syscall_return_callback on_return_callback;
    void *on_return_context;
    int execve_id;
    int abi_;
    pt_regs regs;
    bool regs_changed;
    std::map<pid_t, int> syscall_;
    bool use_peekdata = false;
    virtual char *readstr_peekdata(unsigned long addr, size_t max_size);
#if PTBOX_FREEBSD
    linux_pt_reg bsd_converted_regs;
#endif
    friend class pt_process;
};
#endif
