#include "ptbox.h"
#include "helper.h"

#include <dirent.h>
#include <errno.h>
#include <signal.h>
#include <unistd.h>
#include <sys/resource.h>
#include <sys/types.h>

#if PTBOX_FREEBSD
#   include <sys/param.h>
#   include <sys/queue.h>
#   include <sys/socket.h>
#   include <sys/sysctl.h>
#   include <libprocstat.h>
#endif

#if defined(__FreeBSD__) || (defined(__APPLE__) && defined(__MACH__))
#   define FD_DIR "/dev/fd"
#else
#   define FD_DIR "/proc/self/fd"
#endif

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
    DIR *d = opendir(FD_DIR);
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

// Borrowing some SYS_getdents64 magic from python's _posixsubprocess.
// Look there for explanation. We don't actually need O_CLOEXEC,
// since this process is single-threaded after fork, and could not
// possibly be exec'd before we close the fd. If it is, we have
// bigger problems than leaking the directory fd.
#ifdef __linux__
#include <sys/syscall.h>
#include <sys/stat.h>
#include <fcntl.h>

struct linux_dirent64 {
    unsigned long long d_ino;
    long long d_off;
    unsigned short d_reclen;
    unsigned char d_type;
    char d_name[256];
};

static void cptbox_closefrom_getdents(int lowfd) {
    int fd_dir = open(FD_DIR, O_RDONLY, 0);
    if (fd_dir == -1) {
        cptbox_closefrom_brute(lowfd);
    } else {
        char buffer[sizeof(struct linux_dirent64)];
        int bytes;
        while ((bytes = syscall(SYS_getdents64, fd_dir,
                                (struct linux_dirent64 *)buffer,
                                sizeof(buffer))) > 0) {
            struct linux_dirent64 *entry;
            int offset;
            for (offset = 0; offset < bytes; offset += entry->d_reclen) {
                int fd;
                entry = (struct linux_dirent64 *)(buffer + offset);
                if ((fd = pos_int_from_ascii(entry->d_name)) < 0)
                    continue;  /* Not a number. */
                if (fd != fd_dir && fd >= lowfd)
                    cptbox_close_fd(fd);
            }
        }
        close(fd_dir);
    }
}
#endif

void cptbox_closefrom(int lowfd) {
#if defined(__FreeBSD__) && __FreeBSD__ >= 8
    closefrom(lowfd);
#elif defined(F_CLOSEM)
    fcntl(fd, F_CLOSEM, 0);
#elif defined(__linux__)
    cptbox_closefrom_getdents(lowfd);
#else
    cptbox_closefrom_dirent(lowfd);
#endif
}

int bsd_get_proc_cwd(pid_t pid, char *buf, int cb) {
#if PTBOX_FREEBSD
    int ret = 0;
    unsigned kp_cnt;
    struct procstat *procstat;
    struct kinfo_proc *kp;
    struct filestat_list *head;
    struct filestat *fst;

    procstat = procstat_open_sysctl();
    if (procstat) {
        kp = procstat_getprocs(procstat, KERN_PROC_PID, pid, &kp_cnt);
        if (kp) {
            head = procstat_getfiles(procstat, kp, 0);
            if (head) {
                ret = EPERM; // Most likely you have no access
                STAILQ_FOREACH(fst, head, next) {
                    if (fst->fs_uflags & PS_FST_UFLAG_CDIR) {
                        strlcpy(buf, fst->fs_path, cb);
                        ret = 0;
                        break;
                    }
                }
            } else ret = errno;
            procstat_freeprocs(procstat, kp);
        } else ret = errno;
        procstat_close(procstat);
    } else ret = errno;
    return ret;
#else
    return EOPNOTSUPP;
#endif
}

