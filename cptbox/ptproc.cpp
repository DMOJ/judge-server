#define _BSD_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/ptrace.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>
#include "ptbox.h"

pt_process *pt_alloc_process(pt_debugger *debugger) {
    return new pt_process(debugger);
}

void pt_free_process(pt_process *process) {
    delete process;
}

pt_process::pt_process(pt_debugger *debugger) :
    pid(0), callback(NULL), context(NULL), debugger(debugger)
{
    memset(&exec_time, 0, sizeof exec_time);
    memset(handler, 0, sizeof handler);
    debugger->set_process(this);
}

void pt_process::set_callback(pt_handler_callback callback, void *context) {
    this->callback = callback;
    this->context = context;
}

int pt_process::set_handler(int syscall, int handler) {
    if (syscall >= MAX_SYSCALL || syscall < 0)
        return 1;
    this->handler[syscall] = handler;
    return 0;
}

int pt_process::spawn(pt_fork_handler child, void *context) {
    pid_t pid = fork();
    if (pid == -1)
        return 1;
    if (pid == 0)
        _exit(child(context));
    this->pid = pid;
    debugger->new_process();
    return 0;
}

int pt_process::monitor() {
    bool in_syscall = false;
    struct timespec start, end, delta;
    int status;
    siginfo_t si;

    while (true) {
        clock_gettime(CLOCK_MONOTONIC, &start);
        wait4(pid, &status, 0, &_rusage);
        clock_gettime(CLOCK_MONOTONIC, &end);
        timespec_sub(&end, &start, &delta);
        timespec_add(&exec_time, &delta, &exec_time);

        if (WIFEXITED(status) || WIFSIGNALED(status))
            break;

        if (WIFSTOPPED(status) && WSTOPSIG(status) == SIGTRAP) {
            ptrace(PTRACE_GETSIGINFO, pid, NULL, &si);
            if (si.si_code == SIGTRAP || si.si_code == (SIGTRAP|0x80)) {
                int syscall = debugger->syscall();
                printf("%s syscall %d\n", in_syscall ? "Exit" : "Enter", syscall);
                if (!in_syscall) {
                    switch (handler[syscall]) {
                        case PTBOX_HANDLER_ALLOW:
                            break;
                        case PTBOX_HANDLER_CALLBACK:
                            if (callback(context, syscall))
                                break;
                            // Fall through
                        default:
                            // Default is to kill, safety first.
                            kill(pid, SIGKILL);
                            continue;
                    }
                }
                in_syscall ^= true;
            }
        }
        ptrace(PTRACE_SYSCALL, pid, NULL, NULL);
    }
    return WIFEXITED(status) ? WEXITSTATUS(status) : -WTERMSIG(status);
}
