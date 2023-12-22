#pragma once
#ifndef idABBEC9C1_3EF3_4A45_B187B10060CB9F85
#define idABBEC9C1_3EF3_4A45_B187B10060CB9F85

#include <sys/types.h>

#define PTBOX_SPAWN_FAIL_NO_NEW_PRIVS 202
#define PTBOX_SPAWN_FAIL_SECCOMP      203
#define PTBOX_SPAWN_FAIL_TRACEME      204
#define PTBOX_SPAWN_FAIL_EXECVE       205
#define PTBOX_SPAWN_FAIL_SETAFFINITY  206
#define PTBOX_SPAWN_FAIL_LANDLOCK     207

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
    const char **landlock_read_exact_files;
    const char **landlock_read_exact_dirs;
    const char **landlock_read_recursive_dirs;
    const char **landlock_write_exact_files;
    const char **landlock_write_exact_dirs;
    const char **landlock_write_recursive_dirs;
};

int get_landlock_version();

void cptbox_closefrom(int lowfd);
int cptbox_child_run(const struct child_config *config);

char *bsd_get_proc_cwd(pid_t pid);
char *bsd_get_proc_fdno(pid_t pid, int fdno);

int memory_fd_create(void);
int memory_fd_seal(int fd);

#endif
