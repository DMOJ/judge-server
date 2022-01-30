#pragma once
#ifndef idABBEC9C1_3EF3_4A45_B187B10060CB9F85
#define idABBEC9C1_3EF3_4A45_B187B10060CB9F85

#include <sys/types.h>

#define PTBOX_SPAWN_FAIL_NO_NEW_PRIVS 202
#define PTBOX_SPAWN_FAIL_SECCOMP      203
#define PTBOX_SPAWN_FAIL_TRACEME      204
#define PTBOX_SPAWN_FAIL_EXECVE       205
#define PTBOX_SPAWN_FAIL_SETAFFINITY  206

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
    int *seccomp_handlers;
    // 64 cores ought to be enough for anyone.
    unsigned long cpu_affinity_mask;
};

void cptbox_closefrom(int lowfd);
int cptbox_child_run(const struct child_config *config);

char *bsd_get_proc_cwd(pid_t pid);
char *bsd_get_proc_fdno(pid_t pid, int fdno);

int cptbox_memfd_create(void);
int cptbox_memfd_seal(int fd);

#endif
