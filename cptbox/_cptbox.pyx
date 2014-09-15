from libc.stdio cimport FILE, fopen, fclose, fgets, sprintf
from libc.stdlib cimport atoi, malloc, free, strtoul
from libc.string cimport strncmp, strlen
from posix.unistd cimport close, dup2, getpid, execve
from posix.resource cimport setrlimit, rlimit, rusage, \
    RLIMIT_AS, RLIMIT_DATA, RLIMIT_CPU, RLIMIT_STACK, RLIMIT_CORE
from posix.signal cimport kill
from posix.types cimport pid_t
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
    ctypedef int (*pt_event_callback)(void *context, int event, unsigned long param)

    cdef cppclass pt_process:
        pt_process(pt_debugger *) except +
        void set_callback(pt_handler_callback callback, void* context)
        void set_event_proc(pt_event_callback, void *context)
        int set_handler(int syscall, int handler)
        int spawn(pt_fork_handler, void *context)
        int monitor()
        int getpid()
        double execution_time()
        const rusage *getrusage()

    cdef int MAX_SYSCALL

    cdef int PTBOX_EVENT_ATTACH
    cdef int PTBOX_EVENT_EXITING
    cdef int PTBOX_EVENT_EXITED
    cdef int PTBOX_EVENT_SIGNAL

    cdef int PTBOX_EXIT_NORMAL
    cdef int PTBOX_EXIT_PROTECTION
    cdef int PTBOX_EXIT_SEGFAULT

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

cdef extern from 'sys/resource.h' nogil:
    cdef int RLIMIT_NPROC

cdef extern from 'signal.h' nogil:
    cdef int SIGXCPU

SYSCALL_COUNT = MAX_SYSCALL

cdef struct child_config:
    unsigned long memory # affects only sbrk heap
    unsigned long address_space # affects sbrk and mmap but not all address space is used memory
    unsigned int cpu_time # ask linus how this counts the CPU time because it SIGKILLs way before the real time limit
    int nproc
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

    if config.address_space:
        limit.rlim_cur = limit.rlim_max = config.address_space
        setrlimit(RLIMIT_AS, &limit)

    if config.memory:
        limit.rlim_cur = limit.rlim_max = config.memory
        setrlimit(RLIMIT_DATA, &limit)

    if config.cpu_time:
        limit.rlim_cur = config.cpu_time
        limit.rlim_max = config.cpu_time + 1
        setrlimit(RLIMIT_CPU, &limit)

    if config.nproc >= 0:
        limit.rlim_cur = limit.rlim_max = config.nproc
        setrlimit(RLIMIT_NPROC, &limit)

    limit.rlim_cur = limit.rlim_max = 2 * 1024 * 1024
    setrlimit(RLIMIT_STACK, &limit)
    limit.rlim_cur = limit.rlim_max = 0
    setrlimit(RLIMIT_CORE, &limit)

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

cdef int pt_event_handler(void *context, int event, unsigned long param) nogil:
    return (<Process>context)._event_handler(event, param)

cdef char **alloc_string_array(list):
    cdef char **array = <char**>malloc((len(list) + 1) * sizeof(char*))
    for i, elem in enumerate(list):
        array[i] = elem
    array[len(list)] = NULL
    return array

cpdef unsigned long get_memory(pid_t pid) nogil:
    cdef unsigned long memory = 0
    cdef char path[128]
    cdef char line[128]
    cdef char *start
    cdef FILE* file
    cdef int length

    sprintf(path, '/proc/%d/status', pid)
    file = fopen(path, 'r')
    if file == NULL:
        return 0
    while True:
        if fgets(line, 128, file) == NULL:
            break
        if strncmp(line, "VmHWM:", 6) == 0:
            start = line
            length = strlen(line)
            line[length-3] = '\0'
            while not 48 <= start[0] <= 57:
                start += 1
            memory = strtoul(start, NULL, 0)
            break
    fclose(file)
    return memory


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
    cdef public unsigned long _child_memory, _child_address
    cdef public unsigned int _cpu_time
    cdef public int _nproc
    cdef unsigned long _max_memory

    def __cinit__(self, int bitness, *args, **kwargs):
        self._child_memory = self._child_address = 0
        self._child_stdin = self._child_stdout = self._child_stderr = -1
        self._cpu_time = 0
        self._nproc = -1
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
        self.process.set_event_proc(pt_event_handler, <void*>self)

    def __dealloc__(self):
        del self.debugger
        del self.process

    def _callback(self, syscall):
        return False

    cdef int _syscall_handler(self, int syscall) with gil:
        return self._callback(syscall)

    cdef int _event_handler(self, int event, unsigned long param) nogil:
        if event == PTBOX_EVENT_EXITING or event == PTBOX_EVENT_SIGNAL:
            self._max_memory = get_memory(self.process.getpid())
        if event == PTBOX_EVENT_SIGNAL && param == SIGXCPU:
            with gil:
                import sys
                print>>sys.stderr, 'SIGXCPU in child'
        return 0

    cpdef _handler(self, syscall, handler):
        self.process.set_handler(syscall, handler)

    def _spawn(self, file, args, env=()):
        cdef child_config config
        config.address_space = self._child_address
        config.memory = self._child_memory
        config.cpu_time = self._cpu_time
        config.nproc = self._nproc
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
            if self._exited:
                return self._max_memory
            cdef unsigned long memory = get_memory(self.process.getpid())
            if memory > 0:
                self._max_memory = memory
            return self._max_memory

    property returncode:
        def __get__(self):
            if not self._exited:
                return None
            return self._exitcode