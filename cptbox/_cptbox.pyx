from libc.stdlib cimport atoi, malloc, free
from posix.unistd cimport close, dup2, getpid, execve
from posix.resource cimport setrlimit, rlimit, RLIMIT_AS, rusage
from posix.signal cimport kill
from libc.signal cimport SIGSTOP

cdef extern from 'ptbox.h' nogil:
    cdef cppclass pt_debugger:
        int syscall()
        long arg0()
        long arg1()
        long arg2()
        long arg3()
        long arg4()
        long arg5()
        char *readstr(unsigned long)
        void freestr(char*)

    cdef cppclass pt_debugger32(pt_debugger):
        pass

    cdef cppclass pt_debugger64(pt_debugger):
        pass

    ctypedef int (*pt_handler_callback)(void *context, int syscall)
    ctypedef int (*pt_fork_handler)(void *context)

    cdef cppclass pt_process:
        pt_process(pt_debugger *) except +
        void set_callback(pt_handler_callback callback, void* context)
        int set_handler(int syscall, int handler)
        int spawn(pt_fork_handler, void *context)
        int monitor()
        int getpid()
        double execution_time()
        const rusage *getrusage()

    cdef int MAX_SYSCALL

cdef extern from 'dirent.h' nogil:
    ctypedef struct DIR:
        pass

    cdef struct dirent:
        char* d_name

    dirent* readdir(DIR* dirp)

cdef extern from 'sys/types.h' nogil:
    DIR *opendir(char *name)
    int closedir(DIR* dirp)

cdef extern from 'sys/ptrace.h' nogil:
    long ptrace(int, pid_t, void*, void*)
    cdef int PTRACE_TRACEME


SYSCALL_COUNT = MAX_SYSCALL

cdef struct child_config:
    unsigned long memory
    char *file
    char **argv
    char **envp
    int stdin
    int stdout
    int stderr

cdef int pt_child(void *context) nogil:
    cdef child_config *config = <child_config*> context
    cdef DIR *d = opendir('/proc/self/fd')
    cdef dirent *dir
    cdef rlimit limit

    if config.memory:
        limit.rlim_cur = limit.rlim_max = config.memory
        setrlimit(RLIMIT_AS, &limit)

    if config.stdin >= 0:  dup2(config.stdin, 0)
    if config.stdout >= 0: dup2(config.stdout, 1)
    if config.stderr >= 0: dup2(config.stderr, 2)

    while True:
        dir = readdir(d)
        if dir == NULL:
            break
        fd = atoi(dir.d_name)
        if fd > 2:
            close(fd)
    ptrace(PTRACE_TRACEME, 0, NULL, NULL)
    kill(getpid(), SIGSTOP)
    execve(config.file, config.argv, config.envp)
    return 3306

cdef int pt_syscall_handler(void *context, int syscall) nogil:
    return (<Process>context)._syscall_handler(syscall)

cdef char **alloc_string_array(list):
    cdef char **array = <char**>malloc((len(list) + 1) * sizeof(char*))
    for i, elem in enumerate(list):
        array[i] = elem
    array[len(list)] = NULL
    return array


cdef class Debugger:
    cdef pt_debugger *thisptr

    def syscall(self):
        return self.thisptr.syscall()

    def arg0(self):
        return self.thisptr.arg0()

    def arg1(self):
        return self.thisptr.arg1()

    def arg2(self):
        return self.thisptr.arg2()

    def arg3(self):
        return self.thisptr.arg3()

    def arg4(self):
        return self.thisptr.arg4()

    def arg5(self):
        return self.thisptr.arg5()

    def uarg0(self):
        return <unsigned long>self.thisptr.arg0()

    def uarg1(self):
        return <unsigned long>self.thisptr.arg1()

    def uarg2(self):
        return <unsigned long>self.thisptr.arg2()

    def uarg3(self):
        return <unsigned long>self.thisptr.arg3()

    def uarg4(self):
        return <unsigned long>self.thisptr.arg4()

    def uarg5(self):
        return <unsigned long>self.thisptr.arg5()

    def readstr(self, unsigned long address):
        cdef char* str = self.thisptr.readstr(address)
        pystr = <object>str
        self.thisptr.freestr(str)
        return pystr


cdef class Process:
    cdef pt_debugger *_debugger
    cdef pt_process *process
    cdef public Debugger debugger
    cdef readonly bint _exited
    cdef readonly int _exitcode
    cdef public int _child_stdin, _child_stdout, _child_stderr
    cdef public unsigned long _child_memory

    def __cinit__(self, int bitness, *args, **kwargs):
        self._child_memory = 0
        self._child_stdin = self._child_stdout = self._child_stderr = -1
        if bitness == 32:
            self._debugger = new pt_debugger32()
        elif bitness == 64:
            self._debugger = new pt_debugger64()
        else:
            raise ValueError('Invalid bitness')
        self.debugger = Debugger()
        self.debugger.thisptr = self._debugger
        self.process = new pt_process(self._debugger)
        self.process.set_callback(pt_syscall_handler, <void*>self)

    def __dealloc__(self):
        del self.debugger
        del self.process

    def _callback(self, syscall):
        return False

    cdef int _syscall_handler(self, int syscall) with gil:
        return self._callback(syscall)

    cpdef _handler(self, syscall, handler):
        self.process.set_handler(syscall, handler)

    def _spawn(self, file, args, env=()):
        cdef child_config config
        config.memory = self._child_memory
        config.file = file
        config.stdin = self._child_stdin
        config.stdout = self._child_stdout
        config.stderr = self._child_stderr
        config.argv = alloc_string_array(args)
        config.envp = alloc_string_array(env)
        with nogil:
            if self.process.spawn(pt_child, &config):
                with gil:
                    raise RuntimeError('Failed to spawn child')
        free(config.argv)
        free(config.envp)

    cpdef _monitor(self):
        cdef int exitcode
        with nogil:
            exitcode = self.process.monitor()
        self._exitcode = exitcode
        self._exited = True
        return self._exitcode

    property pid:
        def __get__(self):
            return self.process.getpid()

    property execution_time:
        def __get__(self):
            return self.process.execution_time()

    property cpu_time:
        def __get__(self):
            cdef const rusage *usage = self.process.getrusage()
            return usage.ru_utime.tv_sec + usage.ru_utime.tv_usec / 1000000.

    property max_memory:
        def __get__(self):
            cdef const rusage *usage = self.process.getrusage()
            return usage.ru_maxrss

    property returncode:
        def __get__(self):
            if not self._exited:
                return None
            return self._exitcode