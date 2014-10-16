#define _BSD_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <sys/ptrace.h>
#include "ptbox.h"

int child(void *context) {
    char *envp[] = { NULL };
    ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    kill(getpid(), SIGSTOP);
    execle("/bin/ls", "ls", (char *) NULL, envp);
    return 3306;
}

int pt_syscall_handler(void *context, int syscall) {
    pt_debugger* debugger = (pt_debugger*) context;
    if (syscall == 2) {
        char *file = debugger->readstr((unsigned long) debugger->arg0());
        printf("Opening: %s\n", file);
        debugger->freestr(file);
    }
    return true;
}

int allowed_calls[] = {
    0, 1, 3, 5, 9, 10, 11, 12, 13, 14, 16, 21, 59, 72,
    78, 97, 137, 158, 202, 218, 231, 273,
};

int main() {
    pt_debugger64 *debugger = new pt_debugger64();
    pt_process *process = pt_alloc_process(debugger);

    for (unsigned i = 0; i < sizeof(allowed_calls) / sizeof(int); ++i)
        process->set_handler(allowed_calls[i], PTBOX_HANDLER_ALLOW);
    process->set_handler(2, PTBOX_HANDLER_CALLBACK);
    process->set_callback(pt_syscall_handler, debugger);

    process->spawn(child, NULL);
    printf("Return: %d", process->monitor());
    delete process;
    delete debugger;
    return 0;
}
