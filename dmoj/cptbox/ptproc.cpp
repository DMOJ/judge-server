#define _DEFAULT_SOURCE
#define _BSD_SOURCE

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ptrace.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include <set>

#include "ptbox.h"

pt_process::pt_process(pt_debugger *debugger)
    : pid(0), callback(NULL), context(NULL), debugger(debugger), event_proc(NULL), event_context(NULL),
      _trace_syscalls(true), _initialized(false) {
    memset(&exec_time, 0, sizeof exec_time);
    memset(&start_time, 0, sizeof exec_time);
    memset(&end_time, 0, sizeof exec_time);
    memset(handler, 0, sizeof handler);
    debugger->set_process(this);
}

double pt_process::wall_clock_time() {
    struct timespec now, delta;

    if (!start_time.tv_sec && !start_time.tv_nsec)
        return 0;

    if (end_time.tv_sec || end_time.tv_nsec)
        now = end_time;
    else
        clock_gettime(CLOCK_MONOTONIC, &now);
    timespec_sub(&now, &start_time, &delta);
    return delta.tv_sec + delta.tv_nsec / 1000000000.0;
}

void pt_process::set_callback(pt_handler_callback callback, void *context) {
    this->callback = callback;
    this->context = context;
}

void pt_process::set_event_proc(pt_event_callback callback, void *context) {
    this->event_proc = callback;
    this->event_context = context;
}

int pt_process::set_handler(int abi, int syscall, int handler) {
    if (syscall >= MAX_SYSCALL || syscall < 0)
        return 1;
    this->handler[abi][syscall] = handler;
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

int pt_process::protection_fault(int syscall, int type) {
    dispatch(type, syscall);
    dispatch(PTBOX_EVENT_EXITING, PTBOX_EXIT_PROTECTION);
    killpg(pid, SIGKILL);
#if PTBOX_FREEBSD
    // FreeBSD SIGKILL doesn't under ptrace.
    // ptrace(PT_KILL) doesn't work when not under signal-stop.
    // Solution? Use both!
    ptrace(PT_KILL, pid, (caddr_t) 1, 0);

    // We must also kill the current process being debugged.
    if (debugger->tid != pid)
        ptrace(PT_KILL, debugger->tid, (caddr_t) 1, 0);
#endif
    return PTBOX_EXIT_PROTECTION;
}

int pt_process::monitor() {
    bool in_syscall = false, first = true, spawned = false;
    struct timespec start, end, delta;
    int status, exit_reason = PTBOX_EXIT_NORMAL, err;
    // Set pgid to -this->pid such that -pgid becomes pid, resulting
    // in the initial wait be on the main thread. This allows it a chance
    // of creating a new process group.
    pid_t pid, pgid = -this->pid;
    std::set<pid_t> children;

#if PTBOX_FREEBSD
    struct ptrace_lwpinfo lwpi;
#endif

    while (true) {
        clock_gettime(CLOCK_MONOTONIC, &start);

        pid = wait4(-pgid, &status, __WALL, &_rusage);

        clock_gettime(CLOCK_MONOTONIC, &end);
        timespec_sub(&end, &start, &delta);
        timespec_add(&exec_time, &delta, &exec_time);
        int signal = 0;
        bool trap_next_syscall_event = _trace_syscalls && PTBOX_FREEBSD;

        // printf("pid: %d (%d)\n", pid, this->pid);

        if (WIFEXITED(status) || WIFSIGNALED(status)) {
            if (first || pid == pgid)
                break;
            else {
                children.erase(pid);
                // printf("Thread/Process exit: %d\n", pid);
                continue;
            }
        }

#if PTBOX_FREEBSD
        ptrace(PT_LWPINFO, pid, (caddr_t) &lwpi, sizeof lwpi);

        // if (lwpi.pl_flags & PL_FLAG_FORKED)
        //    printf("Created process: %d\n", lwpi.pl_child_pid);

        if (lwpi.pl_flags & PL_FLAG_CHILD) {
            ptrace(PT_FOLLOW_FORK, pid, 0, 1);
            children.insert(pid);
            // printf("Started process: %d\n", pid);
        }
#endif

        if (first) {
            start_time = start;
            dispatch(PTBOX_EVENT_ATTACH, 0);

#if PTBOX_FREEBSD
            // PTRACE_O_TRACESYSGOOD can be replaced by struct ptrace_lwpinfo.pl_flags.
            // No FreeBSD equivalent that I know of
            // * TRACECLONE makes no sense since FreeBSD has no clone(2)
            // * TRACEEXIT... I'm not sure about
            ptrace(PT_FOLLOW_FORK, pid, 0, 1);
#else
            // This is right after SIGSTOP is received:
            ptrace(PTRACE_SETOPTIONS, pid, NULL,
                   PTRACE_O_TRACEEXIT | PTRACE_O_TRACESECCOMP | PTRACE_O_TRACESYSGOOD | PTRACE_O_EXITKILL |
                       PTRACE_O_TRACECLONE | PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK);
#endif
            // We now set the process group to the actual pgid.
            pgid = pid;
        }

        if (!WIFSTOPPED(status)) {
            goto resume_process;
        }

        // printf("%d: WSTOPSIG(status): %d\n", pid, WSTOPSIG(status));
#if PTBOX_FREEBSD
        if (WSTOPSIG(status) == SIGTRAP && lwpi.pl_flags & (PL_FLAG_SCE | PL_FLAG_SCX)) {
            debugger->setpid(pid);
            debugger->update_syscall(&lwpi);
#else
        if ((status >> 8) == (SIGTRAP | PTRACE_EVENT_SECCOMP << 8) || WSTOPSIG(status) == (0x80 | SIGTRAP)) {
            debugger->settid(pid);
#endif
            if ((err = debugger->pre_syscall()) != 0) {
#if !PTBOX_FREEBSD
                // When debugging a multithreaded application, the following sequence of events can happen:
                // 1. Thread #1 does sys_exit_group
                // 2. Thread #2 does any syscall
                // 3. Thread #1 traps, and we handle sys_exit_group
                // 4. sys_exit_group is allowed, all threads are killed
                // 5. Thread #2 traps, and we attempt to read registers
                // 6. Since thread has been killed, this results in ESRCH
                // So we ignore ESRCH. Note that PTRACE_EVENT_EXIT triggers for the thread AFTER this ESRCH,
                // so we can't know in advance if this will happen.
                if (err == ESRCH) {
                    fprintf(stderr, "thread disappeared: %d, ignoring.\n", pid);
                    continue;
                }
#endif
                dispatch(PTBOX_EVENT_PTRACE_ERROR, err);
                exit_reason = protection_fault(-1);
                continue;
            }
#if defined(__FreeBSD_version) && __FreeBSD_version >= 1002501
            int syscall = lwpi.pl_syscall_code;
#else
            int syscall = debugger->syscall();
#endif
#if PTBOX_FREEBSD
            in_syscall = lwpi.pl_flags & PL_FLAG_SCE;
            debugger->_bsd_in_syscall = in_syscall;
#else
            in_syscall = (status >> 8) == (SIGTRAP | PTRACE_EVENT_SECCOMP << 8);
#endif

            // printf("%d: %s syscall %d\n", pid, in_syscall ? "Enter" : "Exit", syscall);
            if (!spawned) {
                if (debugger->is_end_of_first_execve()) {
                    spawned = this->_initialized = true;
                    dispatch(PTBOX_EVENT_INITIAL_EXEC, 0);
                    goto resume_process;
                } else {
                    // Allow any syscalls before the first execve. This allows us to do things
                    // like provide debug messages when ptrace or seccomp initialization fails,
                    // without being hampered by the sandbox.
                    goto resume_process;
                }
            }

            if (in_syscall) {
                if (syscall >= 0 && syscall < MAX_SYSCALL) {
                    switch (handler[debugger->abi()][syscall]) {
                        case PTBOX_HANDLER_ALLOW:
                            break;
                        case PTBOX_HANDLER_CALLBACK:
                            if (callback(context, syscall))
                                break;
                            // printf("Killed by callback: %d\n", syscall);
                            exit_reason = protection_fault(syscall);
                            continue;
                        default:
                            // Default is to kill, safety first.
                            // printf("Killed by DISALLOW or None: %d\n", syscall);
                            exit_reason = protection_fault(syscall);
                            continue;
                    }
                    // We pass any system call that we can't record in our fixed-size array to python.
                    // Python will decide your fate.
                } else if (!callback(context, syscall)) {
                    // printf("Killed by callback: %d\n", syscall);
                    exit_reason = protection_fault(syscall);
                    continue;
                }
            }

            if (debugger->on_return_.count(pid)) {
                if (in_syscall) {
                    // When using seccomp, we'll need to specifically enable tracing after entering
                    // to get the corresponding syscall-exit-stop, which we will use to run on_return.
                    trap_next_syscall_event = true;
                } else {
                    // Fire the on_return handler if we are in a syscall-exit-stop.
                    std::pair<pt_syscall_return_callback, void *> callback = debugger->on_return_[pid];
                    callback.first(callback.second, pid, syscall);
                    debugger->on_return_.erase(pid);
                }
            }

            if ((err = debugger->post_syscall()) != 0) {
#if !PTBOX_FREEBSD
                // Again, it is possible for the process to be killed between pre_syscall and post_syscall.
                // We ignore ESRCH in such a case.
                if (err == ESRCH) {
                    fprintf(stderr, "thread disappeared: %d, ignoring.\n", pid);
                    continue;
                }
#endif
                dispatch(PTBOX_EVENT_PTRACE_ERROR, err);
                exit_reason = protection_fault(syscall, PTBOX_EVENT_UPDATE_FAIL);
                continue;
            }
        } else {
#if PTBOX_FREEBSD
            // No events aside from signal event on FreeBSD
            // (TODO: maybe check for PL_SIGNAL instead of both PL_SIGNAL and PL_NONE?)
            signal = WSTOPSIG(status);

            // Swallow SIGSTOP. This is because no one should send it, nor should it
            // be self-send, hence perfect for implementing shocker.
            if (signal == SIGSTOP)
                signal = 0;
#else
            // We can only find whether a syscall-stop is enter or exit by toggling. However, blind toggling
            // when we receive a syscall-stop does not work. To quote strace:
            // > The rule is that syscall-enter-stop is always followed by syscall-exit-stop,
            // > PTRACE_EVENT stop or tracee's death - no other kinds of ptrace-stop can occur in between.
            // Therefore, we reset the enter/exit toggle if we get something that is not a syscall-stop.
            debugger->tid_reset(pid);

            switch (WSTOPSIG(status)) {
                case SIGTRAP:
                    switch (status >> 16) {
                        case PTRACE_EVENT_EXIT:
                            if (exit_reason != PTBOX_EXIT_NORMAL) {
                                dispatch(PTBOX_EVENT_EXITING, PTBOX_EXIT_NORMAL);
                            }
                            break;
                        case PTRACE_EVENT_CLONE: {
                            unsigned long tid;
                            ptrace(PTRACE_GETEVENTMSG, pid, NULL, &tid);
                            // printf("Created thread: %d\n", tid);
                            break;
                        }
                        case PTRACE_EVENT_FORK:
                        case PTRACE_EVENT_VFORK: {
                            unsigned long npid;
                            ptrace(PTRACE_GETEVENTMSG, pid, NULL, &npid);
                            children.insert(npid);
                            // printf("Created process: %d\n", npid);
                            break;
                        }
                    }
                    break;
                default:
                    signal = WSTOPSIG(status);
            }
#endif

            // Only main process signals are meaningful.
            if (!first && pid == pgid)  // *** Don't set _signal to SIGSTOP if this is the /first/ SIGSTOP
                dispatch(PTBOX_EVENT_SIGNAL, WSTOPSIG(status));
        }
    resume_process:
        // Pass NULL as signal in case of our first SIGSTOP because the runtime tends to resend it, making all our
        // work for naught. Like abort(), it catches the signal, prints something (^Z?) and then resends it.
        // Doing this prevents a second SIGSTOP from being dispatched to our event handler above. ***
#if PTBOX_FREEBSD
        ptrace(trap_next_syscall_event ? PT_SYSCALL : PT_CONTINUE, pid, (caddr_t) 1, first ? 0 : signal);
#else
        ptrace(trap_next_syscall_event ? PTRACE_SYSCALL : PTRACE_CONT, pid, NULL,
               first ? NULL : (void *) (intptr_t) signal);
#endif
        first = false;
    }

    // Children are not permitted to outlive parent, by any meaningful measure.
    for (std::set<pid_t>::const_iterator it = children.begin(); it != children.end(); ++it) {
        kill(*it, SIGKILL);
#if PTBOX_FREEBSD
        ptrace(PT_KILL, *it, (caddr_t) 1, 0);
#endif
    }

    end_time = end;
    dispatch(PTBOX_EVENT_EXITED, exit_reason);
    return WIFEXITED(status) ? WEXITSTATUS(status) : -WTERMSIG(status);
}
