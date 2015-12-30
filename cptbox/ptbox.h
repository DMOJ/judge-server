#pragma once
#ifndef idA6398CB6_D711_4634_9D89FF6B1D215169
#define idA6398CB6_D711_4634_9D89FF6B1D215169

#include <sys/resource.h>
#include <sys/types.h>
#include <sys/time.h>

#define MAX_SYSCALL 546
#define PTBOX_HANDLER_DENY 0
#define PTBOX_HANDLER_ALLOW 1
#define PTBOX_HANDLER_CALLBACK 2
#define PTBOX_HANDLER_STDOUTERR 3

#define PTBOX_EVENT_ATTACH 0
#define PTBOX_EVENT_EXITING 1
#define PTBOX_EVENT_EXITED 2
#define PTBOX_EVENT_SIGNAL 3
#define PTBOX_EVENT_PROTECTION 4

#define PTBOX_EXIT_NORMAL 0
#define PTBOX_EXIT_PROTECTION 1
#define PTBOX_EXIT_SEGFAULT 2

inline void timespec_add(struct timespec *a, struct timespec *b, struct timespec *result) {
    result->tv_sec = a->tv_sec + b->tv_sec ;
    result->tv_nsec = a->tv_nsec + b->tv_nsec ;
    if (result->tv_nsec >= 1000000000L) {
        result->tv_sec++;
        result->tv_nsec = result->tv_nsec - 1000000000L ;
    }
}

inline void timespec_sub(struct timespec *a, struct timespec *b, struct timespec *result) {
    if ((a->tv_sec < b->tv_sec) ||
        ((a->tv_sec == b->tv_sec) &&
         (a->tv_nsec <= b->tv_nsec))) { /* a <= b? */
        result->tv_sec = result->tv_nsec = 0 ;
    } else { /* a > b */
        result->tv_sec = a->tv_sec - b->tv_sec;
        if (a->tv_nsec < b->tv_nsec) {
            result->tv_nsec = a->tv_nsec + 1000000000L - b->tv_nsec ;
            result->tv_sec--; /* Borrow a second-> */
        } else {
            result->tv_nsec = a->tv_nsec - b->tv_nsec ;
        }
    }
}

class pt_debugger;

typedef int (*pt_handler_callback)(void *context, int syscall);
typedef void (*pt_syscall_return_callback)(void *context, int syscall);
typedef int (*pt_fork_handler)(void *context);
typedef int (*pt_event_callback)(void *context, int event, unsigned long param);

class pt_process {
public:
    pt_process(pt_debugger *debugger);
    void set_callback(pt_handler_callback, void *context);
    void set_event_proc(pt_event_callback, void *context);
    int set_handler(int syscall, int handler);
    int spawn(pt_fork_handler child, void *context);
    int monitor();
    int getpid() { return pid; }
    double execution_time() { return exec_time.tv_sec + exec_time.tv_nsec / 1000000000.0; }
    const rusage *getrusage() { return &_rusage; }
protected:
    int dispatch(int event, unsigned long param);
    int protection_fault(int syscall);
private:
    pid_t pid;
    int handler[MAX_SYSCALL];
    pt_handler_callback callback;
    void *context;
    struct timespec exec_time;
    struct rusage _rusage;
    pt_debugger *debugger;
    pt_event_callback event_proc;
    void *event_context;
};

class pt_debugger {
public:
    pt_debugger();

    virtual int syscall() = 0;
    virtual void syscall(int) = 0;
    virtual long result() = 0;
    virtual void result(long) = 0;
    virtual long arg0() = 0;
    virtual long arg1() = 0;
    virtual long arg2() = 0;
    virtual long arg3() = 0;
    virtual long arg4() = 0;
    virtual long arg5() = 0;
    virtual void arg0(long) = 0;
    virtual void arg1(long) = 0;
    virtual void arg2(long) = 0;
    virtual void arg3(long) = 0;
    virtual void arg4(long) = 0;
    virtual void arg5(long) = 0;

    virtual bool is_exit(int syscall) = 0;
    virtual int getpid_syscall() = 0;
    int execve_syscall() { return execve_id; }

    void set_process(pt_process *);
    virtual void new_process();
    virtual char *readstr(unsigned long addr);
    virtual void freestr(char *);
    virtual ~pt_debugger();
    pid_t getpid() { return process->getpid(); }
    void on_return(pt_syscall_return_callback callback, void *context) {
        on_return_callback = callback;
        on_return_context = context;
    }
protected:
    pt_process *process;
    pt_syscall_return_callback on_return_callback;
    void *on_return_context;
    int execve_id;
    friend class pt_process;
};

class pt_debugger_x86 : public pt_debugger {
    long peek_reg(int);
    void poke_reg(int, long);
public:
    pt_debugger_x86();

    virtual int syscall();
    virtual void syscall(int);
    virtual long result();
    virtual void result(long);
    virtual long arg0();
    virtual long arg1();
    virtual long arg2();
    virtual long arg3();
    virtual long arg4();
    virtual long arg5();
    virtual void arg0(long);
    virtual void arg1(long);
    virtual void arg2(long);
    virtual void arg3(long);
    virtual void arg4(long);
    virtual void arg5(long);
    virtual bool is_exit(int syscall);
    virtual int getpid_syscall();
};

class pt_debugger_x64 : public pt_debugger {
protected:
    long peek_reg(int);
    void poke_reg(int, long);
public:
    pt_debugger_x64();

    virtual int syscall();
    virtual void syscall(int);
    virtual long result();
    virtual void result(long);
    virtual long arg0();
    virtual long arg1();
    virtual long arg2();
    virtual long arg3();
    virtual long arg4();
    virtual long arg5();
    virtual void arg0(long);
    virtual void arg1(long);
    virtual void arg2(long);
    virtual void arg3(long);
    virtual void arg4(long);
    virtual void arg5(long);
    virtual bool is_exit(int syscall);
    virtual int getpid_syscall();
};

class pt_debugger_x86_on_x64 : public pt_debugger_x86 {
    long peek_reg(int);
    void poke_reg(int, long);
public:
    pt_debugger_x86_on_x64();

    virtual int syscall();
    virtual void syscall(int);
    virtual long result();
    virtual void result(long);
    virtual long arg0();
    virtual long arg1();
    virtual long arg2();
    virtual long arg3();
    virtual long arg4();
    virtual long arg5();
    virtual void arg0(long);
    virtual void arg1(long);
    virtual void arg2(long);
    virtual void arg3(long);
    virtual void arg4(long);
    virtual void arg5(long);
};

class pt_debugger_x32 : public pt_debugger_x64 {
public:
    virtual int syscall();
};

class pt_debugger_arm : public pt_debugger {
    long peek_reg(int);
    void poke_reg(int, long);
public:
    pt_debugger_arm();

    virtual int syscall();
    virtual void syscall(int);
    virtual long result();
    virtual void result(long);
    virtual long arg0();
    virtual long arg1();
    virtual long arg2();
    virtual long arg3();
    virtual long arg4();
    virtual long arg5();
    virtual void arg0(long);
    virtual void arg1(long);
    virtual void arg2(long);
    virtual void arg3(long);
    virtual void arg4(long);
    virtual void arg5(long);
    virtual bool is_exit(int syscall);
    virtual int getpid_syscall();
};

pt_process *pt_alloc_process(pt_debugger *);
void pt_free_process(pt_process *);
#endif