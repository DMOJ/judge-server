#include "ptbox.h"
#include "helper.h"

#include <dirent.h>
#include <errno.h>
#include <signal.h>
#include <unistd.h>
#include <sys/resource.h>
#include <sys/types.h>

inline void setrlimit2(int resource, rlim_t cur, rlim_t max) {
    rlimit limit;
    limit.rlim_cur = cur;
    limit.rlim_max = max;
    setrlimit(resource, &limit);
}

inline void setrlimit2(int resource, rlim_t limit) {
    setrlimit2(resource, limit, limit);
}

int cptbox_child_run(const struct child_config *config) {
    if (config->address_space)
        setrlimit2(RLIMIT_AS, config->address_space);

    if (config->memory)
        setrlimit2(RLIMIT_DATA, config->memory);

    if (config->cpu_time)
        setrlimit2(RLIMIT_CPU, config->cpu_time, config->cpu_time + 1);

    if (config->nproc >= 0)
        setrlimit2(RLIMIT_NPROC, config->nproc);

    if (config->dir && *config->dir)
        chdir(config->dir);

    setrlimit2(RLIMIT_STACK, RLIM_INFINITY);
    setrlimit2(RLIMIT_CORE, 0);

    if (config->stdin >= 0)  dup2(config->stdin, 0);
    if (config->stdout >= 0) dup2(config->stdout, 1);
    if (config->stderr >= 0) dup2(config->stderr, 2);

    for (int i = 3; i <= config->max_fd; ++i)
        dup2(config->fds[i-3], i);

    cptbox_closefrom(config->max_fd + 1);

    ptrace_traceme();
    kill(getpid(), SIGSTOP);
    execve(config->file, config->argv, config->envp);
    return 3306;
}

// From python's _posixsubprocess
static int pos_int_from_ascii(char *name) {
    int num = 0;
    while (*name >= '0' && *name <= '9') {
        num = num * 10 + (*name - '0');
        ++name;
    }
    if (*name)
        return -1;  /* Non digit found, not a number. */
    return num;
}

static void cptbox_close_fd(int fd) {
    while (close(fd) < 0 && errno == EINTR);
}

static void cptbox_closefrom_brute(int lowfd) {
    int max_fd = sysconf(_SC_OPEN_MAX);
    if (max_fd < 0) max_fd = 16384;
    for (; lowfd <= max_fd; ++lowfd)
        cptbox_close_fd(lowfd);
}

static void cptbox_closefrom_dirent(int lowfd) {
    DIR *d = opendir("/dev/fd");
    dirent *dir;

    if (d) {
        int fd_dirent = dirfd(d);
        errno = 0;
        while ((dir = readdir(d))) {
            int fd = pos_int_from_ascii(dir->d_name);
            if (fd < lowfd || fd == fd_dirent) continue;
            cptbox_close_fd(fd);
            errno = 0;
        }
        if (errno) cptbox_closefrom_brute(lowfd);
        closedir(d);
    } else cptbox_closefrom_brute(lowfd);
}

void cptbox_closefrom(int lowfd) {
#if defined(__FreeBSD__) && __FreeBSD__ >= 8
    closefrom(lowfd);
#elif defined(F_CLOSEM)
    fcntl(fd, F_CLOSEM, 0);
#else
    cptbox_closefrom_dirent(lowfd);
#endif
}
