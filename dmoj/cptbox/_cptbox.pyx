from cpython.exc cimport PyErr_SetFromErrno
from libc.stdio cimport FILE, fopen, fclose, fgets, sprintf
from libc.stdlib cimport malloc, free, strtoul
from libc.string cimport strncmp, strlen
from libc.signal cimport SIGTRAP, SIGXCPU
from libcpp cimport bool
from posix.resource cimport rusage
from posix.types cimport pid_t

__all__ = ['Process', 'Debugger', 'bsd_get_proc_cwd', 'bsd_get_proc_fdno', 'MAX_SYSCALL_NUMBER',
           'AT_FDCWD', 'ALL_ABIS', 'SUPPORTED_ABIS',
           'PTBOX_ABI_X86', 'PTBOX_ABI_X64', 'PTBOX_ABI_X32', 'PTBOX_ABI_ARM', 'PTBOX_ABI_ARM64',
           'PTBOX_ABI_INVALID', 'PTBOX_ABI_COUNT']


cdef extern from 'ptbox.h' nogil:
    # Cross-platform extern
    long ptrace_traceme()

    ctypedef int (*pt_handler_callback)(void *context, int syscall)
    ctypedef void (*pt_syscall_return_callback)(void *context, int syscall)
    ctypedef int (*pt_fork_handler)(void *context)
    ctypedef int (*pt_event_callback)(void *context, int event, unsigned long param)

    cdef cppclass pt_debugger:
        int syscall()
        void syscall(int)
        long result()
        void result(long)
        long arg0()
        long arg1()
        long arg2()
        long arg3()
        long arg4()
        long arg5()
        void arg0(long)
        void arg1(long)
        void arg2(long)
        void arg3(long)
        void arg4(long)
        void arg5(long)
        char *readstr(unsigned long, size_t)
        void freestr(char*)
        pid_t getpid()
        pid_t gettid()
        int getpid_syscall()
        int abi()
        void on_return(pt_syscall_return_callback callback, void *context)

    cdef cppclass pt_process:
        pt_process(pt_debugger *) except +
        void set_callback(pt_handler_callback callback, void* context)
        void set_event_proc(pt_event_callback, void *context)
        int set_handler(int abi, int syscall, int handler)
        bint trace_syscalls()
        void trace_syscalls(bint value)
        int spawn(pt_fork_handler, void *context)
        int monitor()
        int getpid()
        double execution_time()
        double wall_clock_time()
        const rusage *getrusage()
        bint was_initialized()
        bool use_seccomp()
        bool use_seccomp(bool enabled)

    cdef bint PTBOX_FREEBSD
    cdef bint PTBOX_SECCOMP
    cdef int MAX_SYSCALL

    cdef int PTBOX_EVENT_ATTACH
    cdef int PTBOX_EVENT_EXITING
    cdef int PTBOX_EVENT_EXITED
    cdef int PTBOX_EVENT_SIGNAL
    cdef int PTBOX_EVENT_PROTECTION

    cdef int PTBOX_EXIT_NORMAL
    cdef int PTBOX_EXIT_PROTECTION
    cdef int PTBOX_EXIT_SEGFAULT

    cpdef enum:
        PTBOX_ABI_X86
        PTBOX_ABI_X64
        PTBOX_ABI_X32
        PTBOX_ABI_ARM
        PTBOX_ABI_ARM64
        PTBOX_ABI_COUNT
        PTBOX_ABI_INVALID

    cdef bool debugger_supports_abi "pt_debugger::supports_abi" (int)

ALL_ABIS = [PTBOX_ABI_X86, PTBOX_ABI_X64, PTBOX_ABI_X32, PTBOX_ABI_ARM, PTBOX_ABI_ARM64]
assert len(ALL_ABIS) == PTBOX_ABI_COUNT
SUPPORTED_ABIS = list(filter(debugger_supports_abi, ALL_ABIS))

cdef extern from 'helper.h' nogil:
    cdef struct child_config:
        unsigned long memory # affects only sbrk heap
        unsigned long address_space # affects sbrk and mmap but not all address space is used memory
        unsigned int cpu_time # ask linus how this counts the CPU time because it SIGKILLs way before the real time limit
        unsigned long personality # so we can do things like disable ASLR without toasting security on entire system
        int nproc
        int fsize
        char *file
        char *dir
        char **argv
        char **envp
        int stdin_
        int stdout_
        int stderr_
        int max_fd
        int *fds
        bool use_seccomp
        int abi_for_seccomp
        bint *seccomp_whitelist

    void cptbox_closefrom(int lowfd)
    int cptbox_child_run(child_config *)
    char *_bsd_get_proc_cwd "bsd_get_proc_cwd"(pid_t pid)
    char *_bsd_get_proc_fdno "bsd_get_proc_fdno"(pid_t pid, int fdno)


cdef extern from 'fcntl.h' nogil:
    cpdef enum:
        AT_FDCWD

MAX_SYSCALL_NUMBER = MAX_SYSCALL

cdef int pt_child(void *context) nogil:
    cdef child_config *config = <child_config*> context
    return cptbox_child_run(config)

cdef int pt_syscall_handler(void *context, int syscall) nogil:
    return (<Process>context)._syscall_handler(syscall)

cdef void pt_syscall_return_handler(void *context, int syscall) with gil:
    (<Debugger>context)._on_return(syscall)

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

def bsd_get_proc_cwd(pid_t pid):
    cdef char *buf = _bsd_get_proc_cwd(pid)
    if not buf:
        PyErr_SetFromErrno(OSError)
    res = <object>buf
    free(buf)
    return res

def bsd_get_proc_fdno(pid_t pid, int fd):
    cdef char *buf = _bsd_get_proc_fdno(pid, fd)
    if not buf:
        PyErr_SetFromErrno(OSError)
    res = <object>buf
    free(buf)
    return res


cdef class Process


cdef class Debugger:
    cdef pt_debugger *thisptr
    cdef Process process
    cdef object on_return_callback

    def __cinit__(self, Process process):
        self.thisptr = new pt_debugger()
        self.process = process

    def __dealloc__(self):
        del self.thisptr

    property noop_syscall_id:
        def __get__(self):
            raise NotImplementedError()

    property syscall:
        def __get__(self):
            return self.thisptr.syscall()

        def __set__(self, value):
            # When using seccomp, -1 as syscall means "skip"; when we are not,
            # we swap with a harmless syscall without side-effects (getpid).
            if not self.process.use_seccomp and value == -1:
                self.thisptr.syscall(self.noop_syscall_id)
            else:
                self.thisptr.syscall(value)

    property result:
        def __get__(self):
            return self.thisptr.result()

        def __set__(self, value):
            self.thisptr.result(<long>value)

    property uresult:
        def __get__(self):
            return <unsigned long>self.thisptr.result()

        def __set__(self, value):
            self.thisptr.result(<long><unsigned long>value)

    property arg0:
        def __get__(self):
            return self.thisptr.arg0()

        def __set__(self, value):
            self.thisptr.arg0(<long>value)

    property arg1:
        def __get__(self):
            return self.thisptr.arg1()

        def __set__(self, value):
            self.thisptr.arg1(<long>value)

    property arg2:
        def __get__(self):
            return self.thisptr.arg2()

        def __set__(self, value):
            self.thisptr.arg2(<long>value)

    property arg3:
        def __get__(self):
            return self.thisptr.arg3()

        def __set__(self, value):
            self.thisptr.arg3(<long>value)

    property arg4:
        def __get__(self):
            return self.thisptr.arg4()

        def __set__(self, value):
            self.thisptr.arg4(<long>value)

    property arg5:
        def __get__(self):
            return self.thisptr.arg5()

        def __set__(self, value):
            self.thisptr.arg5(<long>value)

    property uarg0:
        def __get__(self):
            return <unsigned long>self.thisptr.arg0()

        def __set__(self, value):
            self.thisptr.arg0(<long><unsigned long>value)

    property uarg1:
        def __get__(self):
            return <unsigned long>self.thisptr.arg1()

        def __set__(self, value):
            self.thisptr.arg1(<long><unsigned long>value)

    property uarg2:
        def __get__(self):
            return <unsigned long>self.thisptr.arg2()

        def __set__(self, value):
            self.thisptr.arg2(<long><unsigned long>value)

    property uarg3:
        def __get__(self):
            return <unsigned long>self.thisptr.arg3()

        def __set__(self, value):
            self.thisptr.arg3(<long><unsigned long>value)

    property uarg4:
        def __get__(self):
            return <unsigned long>self.thisptr.arg4()

        def __set__(self, value):
            self.thisptr.arg4(<long><unsigned long>value)

    property uarg5:
        def __get__(self):
            return <unsigned long>self.thisptr.arg5()

        def __set__(self, value):
            self.thisptr.arg5(<long><unsigned long>value)

    def readstr(self, unsigned long address, size_t max_size=4096):
        cdef char* str = self.thisptr.readstr(address, max_size)
        pystr = <object>str if str != NULL else None
        self.thisptr.freestr(str)
        return pystr

    property tid:
        def __get__(self):
            return self.thisptr.gettid()

    property pid:
        def __get__(self):
            return self.thisptr.getpid()

    property abi:
        def __get__(self):
            return self.thisptr.abi()

    def on_return(self, callback):
        self.on_return_callback = callback
        self.thisptr.on_return(pt_syscall_return_handler, <void*>self)

    cdef _on_return(self, int syscall) with gil:
        self.on_return_callback()
        self.on_return_callback = None


cdef class Process:
    cdef pt_process *process
    cdef public Debugger debugger
    cdef readonly bint _exited
    cdef readonly int _exitcode
    cdef unsigned int _signal
    cdef public int _child_stdin, _child_stdout, _child_stderr
    cdef public unsigned long _child_memory, _child_address, _child_personality
    cdef public unsigned int _cpu_time
    cdef public int _nproc, _fsize
    cdef unsigned long _max_memory

    def create_debugger(self) -> Debugger:
        return Debugger(self)

    def __cinit__(self, *args, **kwargs):
        self._child_memory = self._child_address = 0
        self._child_stdin = self._child_stdout = self._child_stderr = -1
        self._cpu_time = 0
        self._fsize = -1
        self._nproc = -1
        self._signal = 0

        self.debugger = self.create_debugger()
        self.process = new pt_process(self.debugger.thisptr)
        self.process.set_callback(pt_syscall_handler, <void*>self)
        self.process.set_event_proc(pt_event_handler, <void*>self)

    def __dealloc__(self):
        del self.process

    def _callback(self, syscall):
        return False

    cdef int _syscall_handler(self, int syscall) with gil:
        return self._callback(syscall)

    cdef int _event_handler(self, int event, unsigned long param) nogil:
        if not PTBOX_FREEBSD and (event == PTBOX_EVENT_EXITING or event == PTBOX_EVENT_SIGNAL):
            self._max_memory = get_memory(self.process.getpid()) or self._max_memory
        if event == PTBOX_EVENT_PROTECTION:
            with gil:
                self._protection_fault(param)
        if event == PTBOX_EVENT_SIGNAL:
            if param != SIGTRAP:
                self._signal = param
            if param == SIGXCPU:
                with gil:
                    self._cpu_time_exceeded()
        return 0

    cpdef _handler(self, abi, syscall, handler):
        self.process.set_handler(abi, syscall, handler)

    cpdef _protection_fault(self, syscall):
        pass

    cpdef _cpu_time_exceeded(self):
        pass

    cpdef _get_seccomp_abi_whitelist(self):
        raise NotImplementedError()

    cpdef _spawn(self, file, args, env=(), chdir='', fds=None):
        cdef child_config config
        config.argv = NULL
        config.envp = NULL
        config.fds = NULL
        config.seccomp_whitelist = NULL

        try:
            config.address_space = self._child_address
            config.memory = self._child_memory
            config.cpu_time = self._cpu_time
            config.nproc = self._nproc
            config.fsize = self._fsize
            config.personality = self._child_personality
            config.file = file
            config.dir = chdir
            config.stdin_ = self._child_stdin
            config.stdout_ = self._child_stdout
            config.stderr_ = self._child_stderr
            config.argv = alloc_string_array(args)
            config.envp = alloc_string_array(env)
            if fds is None or not len(fds):
                config.max_fd = 2
            else:
                config.max_fd = 2 + len(fds)
                config.fds = <int*>malloc(sizeof(int) * len(fds))
                for i in range(len(fds)):
                    config.fds[i] = fds[i]

            config.use_seccomp = self.use_seccomp
            if config.use_seccomp:
                config.abi_for_seccomp, whitelist = self._get_seccomp_abi_whitelist()
                assert len(whitelist) == MAX_SYSCALL_NUMBER
                config.seccomp_whitelist = <bint*>malloc(sizeof(bint) * MAX_SYSCALL_NUMBER)
                for i in range(MAX_SYSCALL_NUMBER):
                    config.seccomp_whitelist[i] = whitelist[i]

            if self.process.spawn(pt_child, &config):
                raise RuntimeError('failed to spawn child')
        finally:
            free(config.argv)
            free(config.envp)
            free(config.fds)
            free(config.seccomp_whitelist)

    cpdef _monitor(self):
        cdef int exitcode
        with nogil:
            exitcode = self.process.monitor()
        self._exitcode = exitcode
        self._exited = True
        return self._exitcode

    property use_seccomp:
        def __get__(self):
            return self.process.use_seccomp()

        def __set__(self, bool enabled):
            if not self.process.use_seccomp(enabled):
                raise RuntimeError("Can't change whether seccomp is used after process is created.")

    property was_initialized:
        def __get__(self):
            return self.process.was_initialized()

    property _trace_syscalls:
        def __get__(self):
            return self.process.trace_syscalls()

        def __set__(self, bint value):
            self.process.trace_syscalls(value)

    property pid:
        def __get__(self):
            return self.process.getpid()

    property execution_time:
        def __get__(self):
            return self.process.execution_time()

    property wall_clock_time:
        def __get__(self):
            return self.process.wall_clock_time()

    property cpu_time:
        def __get__(self):
            cdef const rusage *usage = self.process.getrusage()
            return usage.ru_utime.tv_sec + usage.ru_utime.tv_usec / 1000000.

    property max_memory:
        def __get__(self):
            if PTBOX_FREEBSD:
                return self.process.getrusage().ru_maxrss
            if self._exited:
                return self._max_memory or self.process.getrusage().ru_maxrss
            cdef unsigned long memory = get_memory(self.process.getpid())
            if memory > 0:
                self._max_memory = memory
            return self._max_memory or self.process.getrusage().ru_maxrss

    property signal:
        def __get__(self):
            if not self._exited:
                return None
            return self._signal if self.was_initialized else 0

    property returncode:
        def __get__(self):
            if not self._exited:
                return None
            return self._exitcode
