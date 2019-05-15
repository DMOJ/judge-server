#pragma once
#ifndef idABBEC9C1_3EF3_4A45_B187B10060CB9F85
#define idABBEC9C1_3EF3_4A45_B187B10060CB9F85

#define DEBUGGER_X86        0
#define DEBUGGER_X64        1
#define DEBUGGER_X86_ON_X64 2
#define DEBUGGER_X32        3
#define DEBUGGER_ARM        4
#define DEBUGGER_ARM64      5

pt_debugger *get_ptdebugger(int type);

struct child_config {
    unsigned long memory;
    unsigned long address_space;
    unsigned int cpu_time;
    unsigned long personality;
    int nproc;
    int fsize;
    char *file;
    char *dir;
    char **argv;
    char **envp;
    int stdin_;
    int stdout_;
    int stderr_;
    int max_fd;
    int *fds;
    int debugger_type;
    int trace_syscalls;
    int *syscall_whitelist;
};

void cptbox_closefrom(int lowfd);
int cptbox_child_run(const struct child_config *config);

char *bsd_get_proc_cwd(pid_t pid);
char *bsd_get_proc_fdno(pid_t pid, int fdno);

#endif
