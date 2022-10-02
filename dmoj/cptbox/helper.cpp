#include "helper.h"
#include "ptbox.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <unistd.h>

#ifdef __FreeBSD__
#include <sys/param.h>
#include <sys/queue.h>
#include <sys/socket.h>
#include <sys/sysctl.h>

#include <libprocstat.h>
#else
#include <sched.h>
// No ASLR on FreeBSD... not as of 11.0, anyway
#include <sys/personality.h>
#include <sys/prctl.h>
#endif

#if defined(__FreeBSD__) || (defined(__APPLE__) && defined(__MACH__))
#define FD_DIR "/dev/fd"
#else
#define FD_DIR "/proc/self/fd"
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
#ifndef __FreeBSD__
    // There is no ASLR on FreeBSD, but disable it elsewhere
    if (config->personality > 0)
        personality(config->personality);

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0))
        return PTBOX_SPAWN_FAIL_NO_NEW_PRIVS;

#ifdef PR_SET_SPECULATION_CTRL  // Since Linux 4.17
    // Turn off Spectre Variant 4 protection in case it is turned on; we don't
    // care if submissions shoot themselves in the foot. Let this be a
    // best-effort attempt, and don't stop the submission from running if the
    // prctl fails.
    prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, PR_SPEC_ENABLE, 0, 0);
#endif
#endif

    if (ptrace_traceme()) {
        perror("ptrace");
        return PTBOX_SPAWN_FAIL_TRACEME;
    }

    if (config->cpu_affinity_mask) {
#if PTBOX_FREEBSD
        return PTBOX_SPAWN_FAIL_SETAFFINITY;
#else
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);

        for (size_t i = 0; i < sizeof(config->cpu_affinity_mask) * 8; i++) {
            if (config->cpu_affinity_mask & (1 << i)) {
                CPU_SET(i, &cpuset);
            }
        }

        if (sched_setaffinity(getpid(), sizeof(cpuset), &cpuset)) {
            perror("sched_setaffinity");
            return PTBOX_SPAWN_FAIL_SETAFFINITY;
        }
#endif
    }

    kill(getpid(), SIGSTOP);

#if !PTBOX_FREEBSD
    scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_TRACE(0));
    if (!ctx) {
        fprintf(stderr, "Failed to initialize seccomp context!");
        goto seccomp_init_fail;
    }

    int rc;
    // By default, the native architecture is added to the filter already, so we add all the non-native ones.
    // This will bloat the filter due to additional architectures, but a few extra compares in the BPF matters
    // very little when syscalls are rare and other overhead is expensive.
    for (uint32_t *arch = pt_debugger::seccomp_non_native_arch_list; *arch; ++arch) {
        if ((rc = seccomp_arch_add(ctx, *arch))) {
            fprintf(stderr, "seccomp_arch_add(%u): %s\n", *arch, strerror(-rc));
            // This failure is not fatal, it'll just cause the syscall to trap anyway.
        }
    }

    for (int syscall = 0; syscall < MAX_SYSCALL; syscall++) {
        int handler = config->seccomp_handlers[syscall];
        if (handler == 0) {
            if ((rc = seccomp_rule_add(ctx, SCMP_ACT_ALLOW, syscall, 0))) {
                fprintf(stderr, "seccomp_rule_add(..., SCMP_ACT_ALLOW, %d): %s\n", syscall, strerror(-rc));
                // This failure is not fatal, it'll just cause the syscall to trap anyway.
            }
        } else if (handler > 0) {
            if ((rc = seccomp_rule_add(ctx, SCMP_ACT_ERRNO(handler), syscall, 0))) {
                fprintf(stderr, "seccomp_rule_add(..., SCMP_ACT_ERRNO(%d), %d): %s\n", handler, syscall, strerror(-rc));
                // This failure is not fatal, it'll just cause the syscall to trap anyway.
            }
        }
    }

    if ((rc = seccomp_load(ctx))) {
        fprintf(stderr, "seccomp_load: %s\n", strerror(-rc));
        goto seccomp_load_fail;
    }

    seccomp_release(ctx);
#endif

    if (config->stdin_ >= 0)
        dup2(config->stdin_, 0);
    if (config->stdout_ >= 0)
        dup2(config->stdout_, 1);
    if (config->stderr_ >= 0)
        dup2(config->stderr_, 2);
    cptbox_closefrom(3);

    // All these limits should be dropped after initializing seccomp, since seccomp allocates
    // memory, and if an arena isn't sufficiently free it could force seccomp into an OOM
    // situation where we'd fail to initialize.
    if (config->address_space)
        setrlimit2(RLIMIT_AS, config->address_space);

    if (config->memory)
        setrlimit2(RLIMIT_DATA, config->memory);

    if (config->cpu_time)
        setrlimit2(RLIMIT_CPU, config->cpu_time, config->cpu_time + 1);

    if (config->nproc >= 0)
        setrlimit2(RLIMIT_NPROC, config->nproc);

    if (config->fsize >= 0)
        setrlimit2(RLIMIT_FSIZE, config->fsize);

    if (config->dir && *config->dir)
        chdir(config->dir);

    setrlimit2(RLIMIT_STACK, RLIM_INFINITY);
    setrlimit2(RLIMIT_CORE, 0);

    execve(config->file, config->argv, config->envp);
    perror("execve");
    return PTBOX_SPAWN_FAIL_EXECVE;

#if !PTBOX_FREEBSD
seccomp_init_fail:
    seccomp_release(ctx);

seccomp_load_fail:
    return PTBOX_SPAWN_FAIL_SECCOMP;
#endif
}

// From python's _posixsubprocess
static int pos_int_from_ascii(char *name) {
    int num = 0;
    while (*name >= '0' && *name <= '9') {
        num = num * 10 + (*name - '0');
        ++name;
    }
    if (*name)
        return -1; /* Non digit found, not a number. */
    return num;
}

static inline void cptbox_close_fd(int fd) {
    while (close(fd) < 0 && errno == EINTR)
        ;
}

static void cptbox_closefrom_brute(int lowfd) {
    int max_fd = sysconf(_SC_OPEN_MAX);
    if (max_fd < 0)
        max_fd = 16384;
    for (; lowfd <= max_fd; ++lowfd)
        cptbox_close_fd(lowfd);
}

static inline void cptbox_closefrom_dirent(int lowfd) {
    DIR *d = opendir(FD_DIR);
    dirent *dir;

    if (d) {
        int fd_dirent = dirfd(d);
        errno = 0;
        while ((dir = readdir(d))) {
            int fd = pos_int_from_ascii(dir->d_name);
            if (fd < lowfd || fd == fd_dirent)
                continue;
            cptbox_close_fd(fd);
            errno = 0;
        }
        if (errno)
            cptbox_closefrom_brute(lowfd);
        closedir(d);
    } else
        cptbox_closefrom_brute(lowfd);
}

// Borrowing some SYS_getdents64 magic from python's _posixsubprocess.
// Look there for explanation. We don't actually need O_CLOEXEC,
// since this process is single-threaded after fork, and could not
// possibly be exec'd before we close the fd. If it is, we have
// bigger problems than leaking the directory fd.
#ifdef __linux__
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/syscall.h>

struct linux_dirent64 {
    unsigned long long d_ino;
    long long d_off;
    unsigned short d_reclen;
    unsigned char d_type;
    char d_name[256];
};

static inline void cptbox_closefrom_getdents(int lowfd) {
    int fd_dir = open(FD_DIR, O_RDONLY, 0);
    if (fd_dir == -1) {
        cptbox_closefrom_brute(lowfd);
    } else {
        char buffer[sizeof(struct linux_dirent64)];
        int bytes;
        while ((bytes = syscall(SYS_getdents64, fd_dir, (struct linux_dirent64 *) buffer, sizeof(buffer))) > 0) {
            struct linux_dirent64 *entry;
            int offset;
            for (offset = 0; offset < bytes; offset += entry->d_reclen) {
                int fd;
                entry = (struct linux_dirent64 *) (buffer + offset);
                if ((fd = pos_int_from_ascii(entry->d_name)) < 0)
                    continue; /* Not a number. */
                if (fd != fd_dir && fd >= lowfd)
                    cptbox_close_fd(fd);
            }
        }
        close(fd_dir);
    }
}
#endif

void cptbox_closefrom(int lowfd) {
#if defined(__FreeBSD__)
    closefrom(lowfd);
#elif defined(__linux__)
    cptbox_closefrom_getdents(lowfd);
#else
    cptbox_closefrom_dirent(lowfd);
#endif
}

char *bsd_get_proc_fd(pid_t pid, int fdflags, int fdno) {
#ifdef __FreeBSD__
    int err = 0;
    char *buf = NULL;

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
                err = EPERM;  // Most likely you have no access
                STAILQ_FOREACH(fst, head, next) {
                    if ((fdflags && fst->fs_uflags & fdflags) || (!fdflags && fst->fs_fd == fdno)) {
                        buf = (char *) malloc(strlen(fst->fs_path) + 1);
                        if (buf)
                            strcpy(buf, fst->fs_path);
                        err = buf ? 0 : ENOMEM;
                        break;
                    }
                }
            } else
                err = errno;
            procstat_freeprocs(procstat, kp);
        } else
            err = errno;
        procstat_close(procstat);
        errno = err;
    }
    return buf;
#else
    errno = EOPNOTSUPP;
    return NULL;
#endif
}

char *bsd_get_proc_cwd(pid_t pid) {
#ifdef __FreeBSD__
    return bsd_get_proc_fd(pid, PS_FST_UFLAG_CDIR, 0);
#else
    errno = EOPNOTSUPP;
    return NULL;
#endif
}

char *bsd_get_proc_fdno(pid_t pid, int fdno) {
    return bsd_get_proc_fd(pid, 0, fdno);
}

int memory_fd_create(void) {
#ifdef __FreeBSD__
    char filename[] = "/tmp/cptbox-memoryfd-XXXXXXXX";
    int fd = mkstemp(filename);
    if (fd > 0)
        unlink(filename);
    return fd;
#else
    return memfd_create("cptbox memory_fd", MFD_ALLOW_SEALING);
#endif
}

int memory_fd_seal(int fd) {
#ifdef __FreeBSD__
    errno = ENOSYS;
    return -1;
#else
    return fcntl(fd, F_ADD_SEALS, F_SEAL_GROW | F_SEAL_SHRINK | F_SEAL_WRITE);
#endif
}
