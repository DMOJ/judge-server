from libc.stdio cimport FILE, fopen, fclose, fgets, sprintf
from libc.stdlib cimport malloc, free, strtoul
from libc.string cimport strncmp, strlen
from libc.signal cimport SIGTRAP, SIGXCPU
from posix.resource cimport rusage
from posix.types cimport pid_t

__all__ = ['Process', 'Debugger', 'MAX_SYSCALL_NUMBER',
           'DEBUGGER_X86', 'DEBUGGER_X64', 'DEBUGGER_X86_ON_X64', 'DEBUGGER_X32', 'DEBUGGER_ARM']


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
        void on_return(pt_syscall_return_callback callback, void *context)

    cdef cppclass pt_debugger_x86(pt_debugger):
        pass

    cdef cppclass pt_debugger_x64(pt_debugger):
        pass

    cdef cppclass pt_debugger_x86_on_x64(pt_debugger):
        pass

    cdef cppclass pt_debugger_x32(pt_debugger):
        pass

    cdef cppclass pt_debugger_arm(pt_debugger):
        pass

    cdef cppclass pt_process:
        pt_process(pt_debugger *) except +
        void set_callback(pt_handler_callback callback, void* context)
        void set_event_proc(pt_event_callback, void *context)
        int set_handler(int syscall, int handler)
        bint trace_syscalls()
        void trace_syscalls(bint value)
        int spawn(pt_fork_handler, void *context)
        int monitor()
        int getpid()
        double execution_time()
        const rusage *getrusage()
        bint was_initialized()

    cdef bint PTBOX_FREEBSD
    cdef int MAX_SYSCALL

    cdef int PTBOX_EVENT_ATTACH
    cdef int PTBOX_EVENT_EXITING
    cdef int PTBOX_EVENT_EXITED
    cdef int PTBOX_EVENT_SIGNAL
    cdef int PTBOX_EVENT_PROTECTION

    cdef int PTBOX_EXIT_NORMAL
    cdef int PTBOX_EXIT_PROTECTION
    cdef int PTBOX_EXIT_SEGFAULT

cdef extern from 'helper.h' nogil:
    cdef struct child_config:
        unsigned long memory # affects only sbrk heap
        unsigned long address_space # affects sbrk and mmap but not all address space is used memory
        unsigned int cpu_time # ask linus how this counts the CPU time because it SIGKILLs way before the real time limit
        int nproc
        char *file
        char *dir
        char **argv
        char **envp
        int stdin
        int stdout
        int stderr
        int max_fd
        int *fds

    void cptbox_closefrom(int lowfd)
    int cptbox_child_run(child_config *)

MAX_SYSCALL_NUMBER = MAX_SYSCALL

cpdef enum:
    DEBUGGER_X86 = 0
    DEBUGGER_X64 = 1
    DEBUGGER_X86_ON_X64 = 2
    DEBUGGER_X32 = 3
    DEBUGGER_ARM = 4

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


cdef class Debugger:
    cdef pt_debugger *thisptr
    cdef object on_return_callback
    cdef int _getpid_syscall
    cdef int _debugger_type

    property type:
        def __get__(self):
            return self._debugger_type

    property getpid_syscall:
        def __get__(self):
            return self._getpid_syscall

    property syscall:
        def __get__(self):
            return self.thisptr.syscall()

        def __set__(self, value):
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
        pystr = <object>str
        self.thisptr.freestr(str)
        return pystr

    property tid:
        def __get__(self):
            return self.thisptr.gettid()

    property pid:
        def __get__(self):
            return self.thisptr.getpid()

    def on_return(self, callback):
        self.on_return_callback = callback
        self.thisptr.on_return(pt_syscall_return_handler, <void*>self)

    cdef _on_return(self, int syscall) with gil:
        self.on_return_callback()
        self.on_return_callback = None


cdef class Process:
    cdef pt_debugger *_debugger
    cdef pt_process *process
    cdef public Debugger debugger
    cdef readonly bint _exited
    cdef readonly int _exitcode
    cdef unsigned int _signal
    cdef public int _child_stdin, _child_stdout, _child_stderr
    cdef public unsigned long _child_memory, _child_address
    cdef public unsigned int _cpu_time
    cdef public int _nproc
    cdef unsigned long _max_memory

    def __cinit__(self, int debugger, debugger_type, *args, **kwargs):
        self._child_memory = self._child_address = 0
        self._child_stdin = self._child_stdout = self._child_stderr = -1
        self._cpu_time = 0
        self._nproc = -1
        self._signal = 0

        if debugger == DEBUGGER_X86:
            self._debugger = new pt_debugger_x86()
        elif debugger == DEBUGGER_X64:
            self._debugger = new pt_debugger_x64()
        elif debugger == DEBUGGER_X86_ON_X64:
            self._debugger = new pt_debugger_x86_on_x64()
        elif debugger == DEBUGGER_X32:
            self._debugger = new pt_debugger_x32()
        elif debugger == DEBUGGER_ARM:
            self._debugger = new pt_debugger_arm()
        else:
            raise ValueError('Unsupported debugger configuration')

        self.debugger = <Debugger?>debugger_type()
        self.debugger.thisptr = self._debugger
        self.debugger._getpid_syscall = self._debugger.getpid_syscall()
        self.debugger._debugger_type = debugger
        self.process = new pt_process(self._debugger)
        self.process.set_callback(pt_syscall_handler, <void*>self)
        self.process.set_event_proc(pt_event_handler, <void*>self)

    def __dealloc__(self):
        del self.process
        del self._debugger

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

    cpdef _handler(self, syscall, handler):
        self.process.set_handler(syscall, handler)

    cpdef _protection_fault(self, syscall):
        pass

    cpdef _cpu_time_exceeded(self):
        pass

    cpdef _spawn(self, file, args, env=(), chdir='', fds=None):
        cdef child_config config
        config.address_space = self._child_address
        config.memory = self._child_memory
        config.cpu_time = self._cpu_time
        config.nproc = self._nproc
        config.file = file
        config.dir = chdir
        config.stdin = self._child_stdin
        config.stdout = self._child_stdout
        config.stderr = self._child_stderr
        config.argv = alloc_string_array(args)
        config.envp = alloc_string_array(env)
        if fds is None or not len(fds):
            config.max_fd = 2
            config.fds = NULL
        else:
            config.max_fd = 2 + len(fds)
            config.fds = <int*>malloc(sizeof(int) * len(fds))
            for i in xrange(len(fds)):
                config.fds[i] = fds[i]
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

    property cpu_time:
        def __get__(self):
            cdef const rusage *usage = self.process.getrusage()
            return usage.ru_utime.tv_sec + usage.ru_utime.tv_usec / 1000000.

    property max_memory:
        def __get__(self):
            if PTBOX_FREEBSD:
                return self.process.getrusage().ru_maxrss
            if self._exited:
                return self._max_memory
            cdef unsigned long memory = get_memory(self.process.getpid())
            if memory > 0:
                self._max_memory = memory
            return self._max_memory

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
