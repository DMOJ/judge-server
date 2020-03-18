#include "ptbox.h"
#include "helper.h"

#include <dirent.h>
#include <errno.h>
#include <signal.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/resource.h>
#include <sys/types.h>

#ifdef __FreeBSD__
#   include <sys/param.h>
#   include <sys/queue.h>
#   include <sys/socket.h>
#   include <sys/sysctl.h>
#   include <libprocstat.h>
#else
// No ASLR on FreeBSD... not as of 11.0, anyway
#   include <sys/personality.h>
#endif

#if defined(__FreeBSD__) || (defined(__APPLE__) && defined(__MACH__))
#   define FD_DIR "/dev/fd"
#else
#   define FD_DIR "/proc/self/fd"
#endif

inline unsigned int get_seccomp_arch(int type) {
    switch (type) {
#ifdef SCMP_ARCH_X86
        case DEBUGGER_X86:
        case DEBUGGER_X86_ON_X64:
            return SCMP_ARCH_X86;
#endif
#ifdef SCMP_ARCH_X86_64
        case DEBUGGER_X64:
            return SCMP_ARCH_X86_64;
#endif
#ifdef SCMP_ARCH_X32
        case DEBUGGER_X32:
            return SCMP_ARCH_X32;
#endif
#ifdef SCMP_ARCH_ARM
        case DEBUGGER_ARM:
            return SCMP_ARCH_ARM;
#endif
#ifdef SCMP_ARCH_AARCH64
        case DEBUGGER_ARM64:
            return SCMP_ARCH_AARCH64;
#endif
    }

    return 0;
}

pt_debugger *get_ptdebugger(int type) {
    switch (type) {
#ifdef HAS_DEBUGGER_X86
        case DEBUGGER_X86:
            return new pt_debugger_x86();
#endif
#ifdef HAS_DEBUGGER_X64
        case DEBUGGER_X64:
            return new pt_debugger_x64();
#endif
#ifdef HAS_DEBUGGER_X86_ON_X64
        case DEBUGGER_X86_ON_X64:
            return new pt_debugger_x86_on_x64();
#endif
#ifdef HAS_DEBUGGER_X32
        case DEBUGGER_X32:
            return new pt_debugger_x32();
#endif
#ifdef HAS_DEBUGGER_ARM
        case DEBUGGER_ARM:
            return new pt_debugger_arm();
#endif
#ifdef HAS_DEBUGGER_ARM64
        case DEBUGGER_ARM64:
            return new pt_debugger_arm64();
#endif
    }
    return NULL;
}

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
#endif

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

#ifdef PR_SET_NO_NEW_PRIVS  // Since Linux 3.5
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0))
        return 202;
#endif

#ifdef PR_SET_SPECULATION_CTRL  // Since Linux 4.17
    // Turn off Spectre Variant 4 protection in case it is turned on; we don't
    // care if submissions shoot themselves in the foot. Let this be a
    // best-effort attempt, and don't stop the submission from running if the
    // prctl fails.
    prctl(PR_SET_SPECULATION_CTRL, PR_SPEC_STORE_BYPASS, PR_SPEC_ENABLE, 0, 0);
#endif

    if (config->stdin_ >= 0)  dup2(config->stdin_, 0);
    if (config->stdout_ >= 0) dup2(config->stdout_, 1);
    if (config->stderr_ >= 0) dup2(config->stderr_, 2);

    for (int i = 3; i <= config->max_fd; ++i)
        dup2(config->fds[i-3], i);

    cptbox_closefrom(config->max_fd + 1);

    if (ptrace_traceme())
        return 204;

    kill(getpid(), SIGSTOP);

#if PTBOX_SECCOMP
    if (config->trace_syscalls) {
        scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_TRACE(0));
        if (!ctx) return 203;

        unsigned int child_arch = get_seccomp_arch(config->debugger_type);

        if (seccomp_arch_exist(ctx, child_arch) == -EEXIST &&
            seccomp_arch_add(ctx, child_arch) != 0) {
            return 203;
        }

        for (int syscall = 0; syscall < MAX_SYSCALL; syscall++) {
            if (config->syscall_whitelist[syscall]) {
                seccomp_rule_add(ctx, SCMP_ACT_ALLOW, syscall, 0);
            }
        }

        if (seccomp_load(ctx)) return 203;
        seccomp_release(ctx);
    }
#endif

    execve(config->file, config->argv, config->envp);
    return 205;
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
                err = EPERM; // Most likely you have no access
                STAILQ_FOREACH(fst, head, next) {
                    if ((fdflags && fst->fs_uflags & fdflags) ||
                       (!fdflags && fst->fs_fd == fdno)) {
                        buf = (char*) malloc(strlen(fst->fs_path) + 1);
                        if (buf)
                            strcpy(buf, fst->fs_path);
                        err = buf ? 0 : ENOMEM;
                        break;
                    }
                }
            } else err = errno;
            procstat_freeprocs(procstat, kp);
        } else err = errno;
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
