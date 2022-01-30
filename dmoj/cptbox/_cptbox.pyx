# cython: language_level=3
from cpython.exc cimport PyErr_NoMemory, PyErr_SetFromErrno
from cpython.buffer cimport PyObject_GetBuffer
from cpython.bytes cimport PyBytes_AsString, PyBytes_FromStringAndSize
from libc.stdio cimport FILE, fopen, fclose, fgets, sprintf
from libc.stdlib cimport malloc, free, strtoul
from libc.string cimport strncmp, strlen
from libc.signal cimport SIGTRAP, SIGXCPU
from libcpp cimport bool
from posix.resource cimport rusage
from posix.types cimport pid_t

__all__ = ['Process', 'Debugger', 'bsd_get_proc_cwd', 'bsd_get_proc_fdno', 'MAX_SYSCALL_NUMBER',
           'AT_FDCWD', 'ALL_ABIS', 'SUPPORTED_ABIS', 'NATIVE_ABI',
           'PTBOX_ABI_X86', 'PTBOX_ABI_X64', 'PTBOX_ABI_X32', 'PTBOX_ABI_ARM', 'PTBOX_ABI_ARM64',
           'PTBOX_ABI_FREEBSD_X64', 'PTBOX_ABI_INVALID', 'PTBOX_ABI_COUNT',
           'PTBOX_SPAWN_FAIL_NO_NEW_PRIVS', 'PTBOX_SPAWN_FAIL_SECCOMP', 'PTBOX_SPAWN_FAIL_TRACEME',
           'PTBOX_SPAWN_FAIL_EXECVE', 'PTBOX_SPAWN_FAIL_SETAFFINITY']


cdef extern from 'ptbox.h' nogil:
    # Cross-platform extern
    long ptrace_traceme()

    ctypedef int (*pt_handler_callback)(void *context, int syscall)
    ctypedef void (*pt_syscall_return_callback)(void *context, pid_t pid, int syscall)
    ctypedef int (*pt_fork_handler)(void *context)
    ctypedef int (*pt_event_callback)(void *context, int event, unsigned long param)

    cdef cppclass pt_debugger:
        int syscall()
        int syscall(int)
        long result()
        void result(long)
        long error()
        void error(long)
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
        bool readbytes(unsigned long, char *, size_t)
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

    cdef bint PTBOX_FREEBSD
    cdef int MAX_SYSCALL

    cdef int PTBOX_EVENT_ATTACH
    cdef int PTBOX_EVENT_EXITING
    cdef int PTBOX_EVENT_EXITED
    cdef int PTBOX_EVENT_SIGNAL
    cdef int PTBOX_EVENT_PROTECTION
    cdef int PTBOX_EVENT_PTRACE_ERROR
    cdef int PTBOX_EVENT_UPDATE_FAIL
    cdef int PTBOX_EVENT_INITIAL_EXEC

    cdef int PTBOX_EXIT_NORMAL
    cdef int PTBOX_EXIT_PROTECTION

    cpdef enum:
        PTBOX_ABI_X86
        PTBOX_ABI_X64
        PTBOX_ABI_X32
        PTBOX_ABI_ARM
        PTBOX_ABI_ARM64
        PTBOX_ABI_FREEBSD_X64
        PTBOX_ABI_COUNT
        PTBOX_ABI_INVALID

    cdef int native_abi "pt_debugger::native_abi"
    cdef bool debugger_supports_abi "pt_debugger::supports_abi" (int)

ALL_ABIS = [PTBOX_ABI_X86, PTBOX_ABI_X64, PTBOX_ABI_X32, PTBOX_ABI_ARM, PTBOX_ABI_ARM64, PTBOX_ABI_FREEBSD_X64]
assert len(ALL_ABIS) == PTBOX_ABI_COUNT
SUPPORTED_ABIS = list(filter(debugger_supports_abi, ALL_ABIS))
NATIVE_ABI = native_abi

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
        int abi_for_seccomp
        int *seccomp_handlers
        unsigned long cpu_affinity_mask

    void cptbox_closefrom(int lowfd)
    int cptbox_child_run(child_config *)
    char *_bsd_get_proc_cwd "bsd_get_proc_cwd"(pid_t pid)
    char *_bsd_get_proc_fdno "bsd_get_proc_fdno"(pid_t pid, int fdno)

    cpdef enum:
        PTBOX_SPAWN_FAIL_NO_NEW_PRIVS
        PTBOX_SPAWN_FAIL_SECCOMP
        PTBOX_SPAWN_FAIL_TRACEME
        PTBOX_SPAWN_FAIL_EXECVE
        PTBOX_SPAWN_FAIL_SETAFFINITY

    int cptbox_memfd_create()
    int cptbox_memfd_seal(int fd)


cdef extern from 'fcntl.h' nogil:
    cpdef enum:
        AT_FDCWD

cdef extern from "errno.h":
    int errno

MAX_SYSCALL_NUMBER = MAX_SYSCALL

cdef int pt_child(void *context) noexcept nogil:
    cdef child_config *config = <child_config*> context
    return cptbox_child_run(config)

cdef int pt_syscall_handler(void *context, int syscall) noexcept nogil:
    return (<Process>context)._syscall_handler(syscall)
    # Note that upon exception, this function is guaranteed to return due to noexcept.
    # Cython will swallow any exception raised and print to stderr, then make this function return 0,
    # which means to deny syscall.

cdef void pt_syscall_return_handler(void *context, pid_t pid, int syscall) noexcept with gil:
    (<Debugger>context)._on_return(pid, syscall)

cdef int pt_event_handler(void *context, int event, unsigned long param) noexcept nogil:
    return (<Process>context)._event_handler(event, param)

cdef char **alloc_byte_array(list list) except NULL:
    cdef size_t length = len(list)
    cdef char **array = <char**>malloc((length + 1) * sizeof(char*))
    if not array:
        PyErr_NoMemory()
    for i in range(length):
        array[i] = list[i]
    array[length] = NULL
    return array

cdef unsigned long get_memory(pid_t pid) nogil:
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
            line[length-3] = b'\0'
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

def memfd_create():
    cdef int fd = cptbox_memfd_create()
    if fd < 0:
        PyErr_SetFromErrno(OSError)
    return fd

def memfd_seal(int fd):
    cdef int result = cptbox_memfd_seal(fd)
    if result == -1:
        PyErr_SetFromErrno(OSError)

cdef class Process


cdef class Debugger:
    cdef pt_debugger *thisptr
    cdef Process process
    cdef object on_return_callback

    def __cinit__(self, Process process):
        self.thisptr = new pt_debugger()
        self.process = process
        self.on_return_callback = {}

    def __dealloc__(self):
        del self.thisptr

    @property
    def noop_syscall_id(self):
        raise NotImplementedError()

    @property
    def syscall(self):
        return self.thisptr.syscall()

    @syscall.setter
    def syscall(self, int value):
        if PTBOX_FREEBSD and value == -1:
            value = self.noop_syscall_id
        global errno
        errno = self.thisptr.syscall(value)
        if errno:
            PyErr_SetFromErrno(OSError)

    @property
    def result(self):
        return self.thisptr.result()

    @result.setter
    def result(self, value):
        self.thisptr.result(<long>value)

    @property
    def uresult(self):
        return <unsigned long>self.thisptr.result()

    @uresult.setter
    def uresult(self, value):
        self.thisptr.result(<long><unsigned long>value)

    @property
    def errno(self):
        return <long>self.thisptr.error()

    @errno.setter
    def errno(self, value):
        self.thisptr.error(<long>value)

    @property
    def arg0(self):
        return self.thisptr.arg0()

    @arg0.setter
    def arg0(self, value):
        self.thisptr.arg0(<long>value)

    @property
    def arg1(self):
        return self.thisptr.arg1()

    @arg1.setter
    def arg1(self, value):
        self.thisptr.arg1(<long>value)

    @property
    def arg2(self):
        return self.thisptr.arg2()

    @arg2.setter
    def arg2(self, value):
        self.thisptr.arg2(<long>value)

    @property
    def arg3(self):
        return self.thisptr.arg3()

    @arg3.setter
    def arg3(self, value):
        self.thisptr.arg3(<long>value)

    @property
    def arg4(self):
        return self.thisptr.arg4()

    @arg4.setter
    def arg4(self, value):
        self.thisptr.arg4(<long>value)

    @property
    def arg5(self):
        return self.thisptr.arg5()

    @arg5.setter
    def arg5(self, value):
        self.thisptr.arg5(<long>value)

    @property
    def uarg0(self):
        return <unsigned long>self.thisptr.arg0()

    @uarg0.setter
    def uarg0(self, value):
        self.thisptr.arg0(<long><unsigned long>value)

    @property
    def uarg1(self):
        return <unsigned long>self.thisptr.arg1()

    @uarg1.setter
    def uarg1(self, value):
        self.thisptr.arg1(<long><unsigned long>value)

    @property
    def uarg2(self):
        return <unsigned long>self.thisptr.arg2()

    @uarg2.setter
    def uarg2(self, value):
        self.thisptr.arg2(<long><unsigned long>value)

    @property
    def uarg3(self):
        return <unsigned long>self.thisptr.arg3()

    @uarg3.setter
    def uarg3(self, value):
        self.thisptr.arg3(<long><unsigned long>value)

    @property
    def uarg4(self):
        return <unsigned long>self.thisptr.arg4()

    @uarg4.setter
    def uarg4(self, value):
        self.thisptr.arg4(<long><unsigned long>value)

    @property
    def uarg5(self):
        return <unsigned long>self.thisptr.arg5()

    @uarg5.setter
    def uarg5(self, value):
        self.thisptr.arg5(<long><unsigned long>value)

    def readstr(self, unsigned long address, size_t max_size=4096):
        cdef char* str = self.thisptr.readstr(address, max_size)
        pystr = <object>str if str != NULL else None
        self.thisptr.freestr(str)
        return pystr

    def readbytes(self, unsigned long address, size_t size):
        buffer = PyBytes_FromStringAndSize(NULL, size)
        if not self.thisptr.readbytes(address, PyBytes_AsString(buffer), size):
            PyErr_SetFromErrno(OSError)
        return buffer

    @property
    def tid(self):
        return self.thisptr.gettid()

    @property
    def pid(self):
        return self.thisptr.getpid()

    @property
    def abi(self):
        return self.thisptr.abi()

    def on_return(self, callback):
        self.on_return_callback[self.tid] = callback
        self.thisptr.on_return(pt_syscall_return_handler, <void*>self)

    cdef _on_return(self, pid_t pid, int syscall) with gil:
        self.on_return_callback[pid]()
        del self.on_return_callback[pid]


cdef class Process:
    cdef pt_process *process
    cdef public Debugger debugger
    cdef readonly bint _exited
    cdef readonly int _exitcode
    cdef public int _child_stdin, _child_stdout, _child_stderr
    cdef public unsigned long _child_memory, _child_address, _child_personality
    cdef public unsigned int _cpu_time
    cdef public int _nproc, _fsize
    cdef public unsigned long _cpu_affinity_mask
    cdef unsigned long _max_memory
    cdef unsigned long _init_nvcsw, _init_nivcsw

    cpdef Debugger create_debugger(self):
        return Debugger(self)

    def __cinit__(self, *args, **kwargs):
        self._child_memory = self._child_address = 0
        self._child_stdin = self._child_stdout = self._child_stderr = -1
        self._cpu_time = 0
        self._fsize = -1
        self._nproc = -1
        self._cpu_affinity_mask = 0
        self._init_nvcsw = self._init_nivcsw = 0

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
        cdef const rusage *usage

        if not PTBOX_FREEBSD and (event == PTBOX_EVENT_EXITING or event == PTBOX_EVENT_SIGNAL):
            self._max_memory = get_memory(self.process.getpid()) or self._max_memory
        if event == PTBOX_EVENT_PROTECTION:
            with gil:
                self._protection_fault(<long>param, is_update=False)
        if event == PTBOX_EVENT_UPDATE_FAIL:
            with gil:
                self._protection_fault(<long>param, is_update=True)
        if event == PTBOX_EVENT_PTRACE_ERROR:
            with gil:
                self._ptrace_error(param)
        if event == PTBOX_EVENT_SIGNAL:
            if param == SIGXCPU:
                with gil:
                    self._cpu_time_exceeded()
        if event == PTBOX_EVENT_INITIAL_EXEC:
            usage = self.process.getrusage()
            self._init_nvcsw = usage.ru_nvcsw
            self._init_nivcsw = usage.ru_nivcsw
        return 0

    cpdef _handler(self, abi, syscall, handler):
        self.process.set_handler(abi, syscall, handler)

    cpdef _protection_fault(self, syscall, is_update):
        pass

    cpdef _ptrace_error(self, errno):
        pass

    cpdef _cpu_time_exceeded(self):
        pass

    cpdef _get_seccomp_handlers(self):
        return [-1] * MAX_SYSCALL

    cpdef _spawn(self, file, args, env=(), chdir=''):
        cdef child_config config
        config.argv = NULL
        config.envp = NULL
        config.seccomp_handlers = NULL

        try:
            config.address_space = self._child_address
            config.memory = self._child_memory
            config.cpu_time = self._cpu_time
            config.nproc = self._nproc
            config.fsize = self._fsize
            config.personality = self._child_personality
            config.cpu_affinity_mask = self._cpu_affinity_mask
            config.file = file
            config.dir = chdir
            config.stdin_ = self._child_stdin
            config.stdout_ = self._child_stdout
            config.stderr_ = self._child_stderr
            config.argv = alloc_byte_array(args)
            config.envp = alloc_byte_array(env)

            if not PTBOX_FREEBSD:
                handlers = self._get_seccomp_handlers()
                assert len(handlers) == MAX_SYSCALL

                config.seccomp_handlers = <int*>malloc(sizeof(int) * MAX_SYSCALL)
                if not config.seccomp_handlers:
                    PyErr_NoMemory()

                for i in range(MAX_SYSCALL):
                    config.seccomp_handlers[i] = handlers[i]

            if self.process.spawn(pt_child, &config):
                raise RuntimeError('failed to spawn child')
        finally:
            free(config.argv)
            free(config.envp)
            free(config.seccomp_handlers)

    cpdef _monitor(self):
        cdef int exitcode
        with nogil:
            exitcode = self.process.monitor()
        self._exitcode = exitcode
        self._exited = True
        return self._exitcode

    @property
    def was_initialized(self):
        return self.process.was_initialized()

    @property
    def _trace_syscalls(self):
        return self.process.trace_syscalls()

    @_trace_syscalls.setter
    def _trace_syscalls(self, bint value):
        self.process.trace_syscalls(value)

    @property
    def pid(self):
        return self.process.getpid()

    @property
    def execution_time(self):
        return self.process.execution_time()

    @property
    def wall_clock_time(self):
        return self.process.wall_clock_time()

    @property
    def cpu_time(self):
        cdef const rusage *usage = self.process.getrusage()
        return usage.ru_utime.tv_sec + usage.ru_utime.tv_usec / 1000000.

    @property
    def max_memory(self):
        if PTBOX_FREEBSD:
            return self.process.getrusage().ru_maxrss
        if self._exited:
            return self._max_memory or self.process.getrusage().ru_maxrss
        cdef unsigned long memory = get_memory(self.process.getpid())
        if memory > 0:
            self._max_memory = memory
        return self._max_memory or self.process.getrusage().ru_maxrss

    @property
    def context_switches(self):
        cdef const rusage *usage = self.process.getrusage()
        return (usage.ru_nvcsw - self._init_nvcsw, usage.ru_nivcsw - self._init_nivcsw)

    @property
    def signal(self):
        if not self._exited:
            return None

        if not self.process.was_initialized():
            return None

        if self._exitcode >= 0:
            return None

        return -self._exitcode

    @property
    def returncode(self):
        if not self._exited:
            return None
        return self._exitcode


cdef class BufferProxy:
    def _get_real_buffer(self):
        raise NotImplementedError

    def __getbuffer__(self, Py_buffer *buffer, int flags):
        PyObject_GetBuffer(self._get_real_buffer(), buffer, flags)
