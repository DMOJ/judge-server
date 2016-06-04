#define _BSD_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <sys/ptrace.h>
#include <sys/resource.h>
#include "ptbox.h"

int child(void *context) {
    char *envp[] = { NULL };
    ptrace(PTRACE_TRACEME, 0, NULL, NULL);
    kill(getpid(), SIGSTOP);
    execle("/bin/ls", "ls", (char *) NULL, envp);
    return 3306;
}

void pt_syscall_return(void *context, int syscall) {
    pt_debugger* debugger = (pt_debugger*) context;
    printf("Returning from: %d: 0x%016lx\n", syscall, debugger->result());
}

int pt_syscall_handler(void *context, int syscall) {
    pt_debugger* debugger = (pt_debugger*) context;
    if (syscall == 5) {
        char *file = debugger->readstr((unsigned long) debugger->arg0(), 4096);
        printf("Opening: %s\n", file);
        debugger->freestr(file);
    }
    debugger->on_return(pt_syscall_return, context);
    return true;
}

int main() {
    pt_debugger32 *debugger = new pt_debugger32();
    pt_process *process = pt_alloc_process(debugger);

    for (unsigned i = 0; i < MAX_SYSCALL; ++i)
        process->set_handler(i, PTBOX_HANDLER_ALLOW);
    process->set_handler(5, PTBOX_HANDLER_CALLBACK);
    process->set_callback(pt_syscall_handler, debugger);

    process->spawn(child, NULL);
    printf("Return: %d", process->monitor());
    delete process;
    delete debugger;
    return 0;
}
