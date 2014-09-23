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
    pid(0), callback(NULL), context(NULL), debugger(debugger),
    event_proc(NULL), event_context(NULL)
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
    if (pid == 0)
        _exit(child(context));
    this->pid = pid;
    debugger->new_process();
    return 0;
}

int pt_process::monitor() {
    bool in_syscall = false, first = true;
    struct timespec start, end, delta;
    int status, exit_reason = PTBOX_EXIT_NORMAL;
    siginfo_t si;

    while (true) {
        clock_gettime(CLOCK_MONOTONIC, &start);
        wait4(pid, &status, 0, &_rusage);
        clock_gettime(CLOCK_MONOTONIC, &end);
        timespec_sub(&end, &start, &delta);
        timespec_add(&exec_time, &delta, &exec_time);

        if (WIFEXITED(status) || WIFSIGNALED(status))
            break;

        if (first)
            dispatch(PTBOX_EVENT_ATTACH, 0);

        if (WIFSTOPPED(status)) {
            if (WSTOPSIG(status) == SIGTRAP) {
                ptrace(PTRACE_GETSIGINFO, pid, NULL, &si);
                if (si.si_code == SIGTRAP || si.si_code == (SIGTRAP|0x80)) {
                    int syscall = debugger->syscall();
                    //printf("%s syscall %d\n", in_syscall ? "Exit" : "Enter", syscall);
                    if (!in_syscall) {
                        switch (handler[syscall]) {
                            case PTBOX_HANDLER_ALLOW:
                                break;
                            case PTBOX_HANDLER_CALLBACK:
                                if (callback(context, syscall))
                                    break;
                                //printf("Killed by callback: %d\n", syscall);
                                dispatch(PTBOX_EVENT_PROTECTION, syscall);
                                dispatch(PTBOX_EVENT_EXITING, exit_reason = PTBOX_EXIT_PROTECTION);
                                kill(pid, SIGKILL);
                                continue;
                            default:
                                // Default is to kill, safety first.
                                //printf("Killed by DISALLOW or None: %d\n", syscall);
                                dispatch(PTBOX_EVENT_PROTECTION, syscall);
                                dispatch(PTBOX_EVENT_EXITING, exit_reason = PTBOX_EXIT_PROTECTION);
                                kill(pid, SIGKILL);
                                continue;
                        }
                        if (debugger->is_exit(syscall))
                            dispatch(PTBOX_EVENT_EXITING, PTBOX_EXIT_NORMAL);
                    }
                    in_syscall ^= true;
                }
            } else {
                switch (WSTOPSIG(status)) {
                    case SIGSEGV:
                        dispatch(PTBOX_EVENT_EXITING, exit_reason = PTBOX_EXIT_SEGFAULT);
                        puts("Child Segfault");
                        kill(pid, SIGKILL);
                        break;
                }
                dispatch(PTBOX_EVENT_SIGNAL, WSTOPSIG(status));
            }
        }
        ptrace(PTRACE_SYSCALL, pid, NULL, NULL);
        first = false;
    }
    dispatch(PTBOX_EVENT_EXITED, exit_reason);
    return WIFEXITED(status) ? WEXITSTATUS(status) : -WTERMSIG(status);
}
