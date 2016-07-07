#define _BSD_SOURCE

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>
#include <sys/ptrace.h>

#include "ptbox.h"

pt_process *pt_alloc_process(pt_debugger *debugger) {
    return new pt_process(debugger);
}

void pt_free_process(pt_process *process) {
    delete process;
}

pt_process::pt_process(pt_debugger *debugger) :
    pid(0), callback(NULL), context(NULL), debugger(debugger),
    event_proc(NULL), event_context(NULL), _trace_syscalls(true),
    _initialized(false)
{
    memset(&exec_time, 0, sizeof exec_time);
    memset(handler, 0, sizeof handler);
    debugger->set_process(this);
}

void pt_process::set_callback(pt_handler_callback callback, void *context) {
    this->callback = callback;
    this->context = context;
}

void pt_process::set_event_proc(pt_event_callback callback, void *context) {
    this->event_proc = callback;
    this->event_context = context;
}

int pt_process::set_handler(int syscall, int handler) {
    if (syscall >= MAX_SYSCALL || syscall < 0)
        return 1;
    this->handler[syscall] = handler;
    return 0;
}

int pt_process::dispatch(int event, unsigned long param) {
    if (event_proc != NULL)
        return event_proc(event_context, event, param);
    return -1;
}

int pt_process::spawn(pt_fork_handler child, void *context) {
    pid_t pid = fork();
    if (pid == -1)
        return 1;
    if (pid == 0) {
        setpgid(0, 0);
        _exit(child(context));
    }
    this->pid = pid;
    debugger->new_process();
    return 0;
}

int pt_process::protection_fault(int syscall) {
    dispatch(PTBOX_EVENT_PROTECTION, syscall);
    dispatch(PTBOX_EVENT_EXITING, PTBOX_EXIT_PROTECTION);
    kill(pid, SIGKILL);
    return PTBOX_EXIT_PROTECTION;
}

int pt_process::monitor() {
    bool in_syscall = false, first = true, spawned = false;
    struct timespec start, end, delta;
    int status, exit_reason = PTBOX_EXIT_NORMAL;
    siginfo_t si;
    // Set pgid to -this->pid such that -pgid becomes pid, resulting
    // in the initial wait be on the main thread. This allows it a chance
    // of creating a new process group.
    pid_t pid, pgid = -this->pid;

    while (true) {
        clock_gettime(CLOCK_MONOTONIC, &start);
        pid = wait4(-pgid, &status, __WALL, &_rusage);
        clock_gettime(CLOCK_MONOTONIC, &end);
        timespec_sub(&end, &start, &delta);
        timespec_add(&exec_time, &delta, &exec_time);
        int signal = 0;

        //printf("pid: %d (%d)\n", pid, this->pid);

        if (WIFEXITED(status) || WIFSIGNALED(status)) {
            if (first || pid == pgid)
                break;
            //else printf("Thread exit: %d\n", pid);
        }

        if (first) {
            dispatch(PTBOX_EVENT_ATTACH, 0);

#if defined(__FreeBSD__)
            // No FreeBSD equivalent that I know of
            // * TRACESYSGOOD is only for bit 7 of SIGTRAP, we can do without
            // * TRACECLONE makes no sense since FreeBSD has no clone(2)
            // * TRACEEXIT... I'm not sure about
#else
            // This is right after SIGSTOP is received:
            ptrace(PTRACE_SETOPTIONS, pid, NULL, PTRACE_O_TRACESYSGOOD | PTRACE_O_TRACEEXIT | PTRACE_O_TRACECLONE);
#endif
            // We now set the process group to the actual pgid.
            pgid = pid;
        }

        if (WIFSTOPPED(status)) {
#if defined(__FreeBSD__)
            // FreeBSD has no PTRACE_O_TRACESYSGOOD equivalent
            if (WSTOPSIG(status) == SIGTRAP) {
else
            if (WSTOPSIG(status) == (0x80 | SIGTRAP)) {
#endif
                debugger->settid(pid);
                int syscall = debugger->syscall();
                in_syscall ^= true;
                //printf("%d: %s syscall %d\n", pid, in_syscall ? "Enter" : "Exit", syscall);

                if (!spawned) {
                    // Does execve not return if the process hits an rlimit and gets SIGKILLed?
                    //
                    // It doesn't. See the strace below.
                    //      $ ulimit -Sv50000
                    //      $ strace ./a.out
                    //      execve("./a.out", ["./a.out"], [/* 17 vars */] <unfinished ...>
                    //      +++ killed by SIGKILL +++
                    //      Killed
                    //
                    // From this we can see that execve doesn't return (<unfinished ...>) if the process fails to
                    // initialize, so we don't need to wait until the next non-execve syscall to set
                    // _initialized to true - if it exited execve, it's good to go.
                    if (!in_syscall && syscall == debugger->execve_syscall())
                        spawned = this->_initialized = true;
                } else if (in_syscall) {
                    if (syscall < MAX_SYSCALL) {
                        switch (handler[syscall]) {
                            case PTBOX_HANDLER_ALLOW:
                                break;
                            case PTBOX_HANDLER_STDOUTERR: {
                                int arg0 = debugger->arg0();
                                if (arg0 != 1 && arg0 != 2)
                                    exit_reason = protection_fault(syscall);
                                break;
                            }
                            case PTBOX_HANDLER_CALLBACK:
                                if (callback(context, syscall))
                                    break;
                                //printf("Killed by callback: %d\n", syscall);
                                exit_reason = protection_fault(syscall);
                                continue;
                            default:
                                // Default is to kill, safety first.
                                //printf("Killed by DISALLOW or None: %d\n", syscall);
                                exit_reason = protection_fault(syscall);
                                continue;
                        }
                    }
                } else if (debugger->on_return_callback) {
                    debugger->on_return_callback(debugger->on_return_context, syscall);
                    debugger->on_return_callback = NULL;
                    debugger->on_return_context = NULL;
                }
            } else {
#if defined(__FreeBSD__)
                // No events aside from signal event on FreeBSD
                // (TODO: maybe check for PL_SIGNAL instead of both PL_SIGNAL and PL_NONE?)
                signal = WSTOPSIG(status);
#else
                switch (WSTOPSIG(status)) {
                    case SIGTRAP:
                        switch (status >> 16) {
                            case PTRACE_EVENT_EXIT:
                                if (exit_reason != PTBOX_EXIT_NORMAL)
                                    dispatch(PTBOX_EVENT_EXITING, PTBOX_EXIT_NORMAL);
                            case PTRACE_EVENT_CLONE: {
                                unsigned long tid;
                                ptrace(PTRACE_GETEVENTMSG, pid, NULL, &tid);
                                //printf("Created thread: %d\n", tid);
                                break;
                            }
                        }
                        break;
                    default:
                        signal = WSTOPSIG(status);
                }
#endif
                if (!first) // *** Don't set _signal to SIGSTOP if this is the /first/ SIGSTOP
                    dispatch(PTBOX_EVENT_SIGNAL, WSTOPSIG(status));
            }
        }
        // Pass NULL as signal in case of our first SIGSTOP because the runtime tends to resend it, making all our
        // work for naught. Like abort(), it catches the signal, prints something (^Z?) and then resends it.
        // Doing this prevents a second SIGSTOP from being dispatched to our event handler above. ***
#if defined(__FreeBSD__)
        ptrace(_trace_syscalls ? PT_SYSCALL : PT_CONTINUE, pid, (caddr_t) 1, first ? 0 : signal);
#else
        ptrace(_trace_syscalls ? PTRACE_SYSCALL : PTRACE_CONT, pid, NULL, first ? NULL : (void*) signal);
#endif
        first = false;
    }
    dispatch(PTBOX_EVENT_EXITED, exit_reason);
    return WIFEXITED(status) ? WEXITSTATUS(status) : -WTERMSIG(status);
}
