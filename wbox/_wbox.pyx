from ctypes import WinError
from os import fdopen, O_RDONLY, O_WRONLY
from msvcrt import open_osfhandle

ctypedef const Py_UNICODE *LPCWSTR
ctypedef Py_UNICODE *LPWSTR
ctypedef const char *LPCSTR
ctypedef char *LPSTR
ctypedef void *HANDLE
ctypedef unsigned long DWORD


cdef extern from 'windows.h' nogil:
    DWORD WaitForSingleObject(HANDLE, DWORD milliseconds)
    cdef DWORD INFINITE, WAIT_TIMEOUT
    bint GetExitCodeProcess(HANDLE, DWORD*)


cdef extern from 'helpers.h' nogil:
    cdef cppclass AutoHandle:
        AutoHandle()
        AutoHandle(HANDLE h)
        HANDLE get()
        HANDLE detach()
        void close()
        void set(HANDLE h)


cdef extern from 'user.h' nogil:
    void WBoxGenerateUserName(LPWSTR buffer, size_t)
    void WBoxGeneratePassword(LPWSTR buffer, size_t)
    void WBoxGeneratePassword(LPWSTR buffer, size_t, LPCWSTR alphabet)

    cdef cppclass CUserManager 'UserManager':
        CUserManager() except +
        CUserManager(LPCWSTR username) except +
        CUserManager(LPCWSTR username, LPCWSTR password) except +

        LPCWSTR username()
        LPCWSTR password()

cdef extern from 'process.h' nogil:
    cdef cppclass JobbedProcessManager:
        JobbedProcessManager() except +

        bint spawn() except +
        bint terminate(unsigned code) except +

        JobbedProcessManager &time(double seconds)
        JobbedProcessManager &memory(size_t bytes)
        JobbedProcessManager &processes(int count)
        JobbedProcessManager &withLogin(LPCWSTR username, LPCWSTR password);
        JobbedProcessManager &command(LPCWSTR cmdline);
        JobbedProcessManager &executable(LPCWSTR executable)
        JobbedProcessManager &directory(LPCWSTR directory)
        JobbedProcessManager &injectX86(LPCWSTR szExecutable)
        JobbedProcessManager &injectX64(LPCWSTR szExecutable)
        JobbedProcessManager &injectFunction(LPCSTR szFunction)
        JobbedProcessManager &environment(LPCWSTR env, size_t cb)

        unsigned long long memory()
        double executionTime()
        bint tle()
        bint mle()
        DWORD return_code()
        bint wait()
        bint wait(DWORD time)

        AutoHandle &process()
        AutoHandle &job()
        AutoHandle &stdIn()
        AutoHandle &stdOut()
        AutoHandle &stdErr()
        
        @staticmethod
        void updateAsmX86(LPCWSTR szExecutable)
        
        @staticmethod
        void updateAsmX64(LPCWSTR szExecutable)


cdef extern from 'firewall.h' nogil:
    cdef cppclass CNetworkManager 'NetworkManager':
        CNetworkManager(LPCWSTR name, LPCWSTR executable) except +


cdef class UserManager:
    cdef CUserManager *thisptr

    def __cinit__(self, username=None, password=None):
        if username is not None and password is not None:
            self.thisptr = new CUserManager(username, password)
        elif username is not None:
            self.thisptr = new CUserManager(username)
        else:
            self.thisptr = new CUserManager()

    def __dealloc__(self):
        if self.thisptr:
            del self.thisptr

    def dispose(self):
        if self.thisptr:
            del self.thisptr
            self.thisptr = NULL

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()

    property username:
        def __get__(self):
            if not self.thisptr:
                raise ValueError('already destroyed')
            return self.thisptr.username()

    property password:
        def __get__(self):
            if not self.thisptr:
                raise ValueError('already destroyed')
            return self.thisptr.password()


cdef class NetworkManager:
    cdef CNetworkManager *thisptr
    cdef unicode _name, _executable

    def __cinit__(self, name, executable):
        if not isinstance(name, unicode):
            name = name.decode('mbcs')
        if not isinstance(executable, unicode):
            executable = executable.decode('mbcs')
        self._name = name
        self._executable = executable
        self.thisptr = new CNetworkManager(name, executable)

    def __dealloc__(self):
        if self.thisptr:
            del self.thisptr

    def dispose(self):
        if self.thisptr:
            del self.thisptr
            self.thisptr = NULL

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()

    property name:
        def __get__(self):
            if not self.thisptr:
                raise ValueError('already destroyed')
            return self._name

    property executable:
        def __get__(self):
            if not self.thisptr:
                raise ValueError('already destroyed')
            return self._executable


cdef class ProcessManager:
    cdef JobbedProcessManager *thisptr
    cdef double _time_limit
    cdef size_t _memory_limit
    cdef int _process_limit
    cdef unicode _username
    cdef unicode _password
    cdef unicode _executable
    cdef unicode _command
    cdef unicode _dir
    cdef unicode _inject32
    cdef unicode _inject64
    cdef str _inject_func
    cdef object _stdin, _stdout, _stderr

    def __cinit__(self, username, password):
        self.thisptr = new JobbedProcessManager()
        self._time_limit = 0
        self._memory_limit = 0
        self._process_limit = 0
        self._username = username
        self._password = password
        self._executable = self._dir = u''
        self._inject32 = self._inject64 = None
        self._inject_func = None
        self._stdin = self._stdout = self._stderr = None
        self.thisptr.withLogin(username, password)

    def __dealloc__(self):
        del self.thisptr

    def spawn(self):
        with nogil:
            if not self.thisptr.spawn():
                with gil:
                    return False
        cdef HANDLE stdin, stdout, stderr
        stdin = self.thisptr.stdIn().detach()
        stdout = self.thisptr.stdOut().detach()
        stderr = self.thisptr.stdErr().detach()
        self._stdin = fdopen(open_osfhandle(<unsigned long long>stdin, O_WRONLY), 'w')
        self._stdout = fdopen(open_osfhandle(<unsigned long long>stdout, O_RDONLY), 'r')
        self._stderr = fdopen(open_osfhandle(<unsigned long long>stderr, O_RDONLY), 'r')

    def terminate(self, code):
        return self.thisptr.terminate(code)

    def wait(self, timeout=None):
        cdef DWORD time, result
        if timeout is not None:
            time = timeout
        else:
            time = INFINITE
        with nogil:
            result = WaitForSingleObject(self.thisptr.process().get(), time)
        return result

    def get_exit_code(self):
        cdef DWORD code
        if WaitForSingleObject(self.thisptr.process().get(), 0) == WAIT_TIMEOUT:
            return None
        else:
            if not GetExitCodeProcess(self.thisptr.process().get(), &code):
                raise WinError()
            return code

    def set_environment(self, unicode memory):
        self.thisptr.environment(memory, len(memory) * sizeof(Py_UNICODE))

    def inherit_environment(self):
        self.thisptr.environment(NULL, 0)

    property stdin:
        def __get__(self):
            return self._stdin

    property stdout:
        def __get__(self):
            return self._stdout

    property stderr:
        def __get__(self):
            return self._stderr

    property time_limit:
        def __get__(self):
            return self._time_limit

        def __set__(self, value):
            self._time_limit = value
            self.thisptr.time(value)

    property memory_limit:
        def __get__(self):
            return self._memory_limit

        def __set__(self, value):
            self._memory_limit = value
            self.thisptr.memory(value)

    property process_limit:
        def __get__(self):
            return self._process_limit

        def __set__(self, value):
            self._process_limit = value
            self.thisptr.processes(value)

    property executable:
        def __get__(self):
            return self._executable

        def __set__(self, value):
            self._executable = value
            self.thisptr.executable(value)

    property command:
        def __get__(self):
            return self._command

        def __set__(self, value):
            self._command = value
            self.thisptr.command(value)

    property dir:
        def __get__(self):
            return self._dir

        def __set__(self, value):
            self._dir = value
            self.thisptr.directory(value)

    property inject32:
        def __get__(self):
            return self._inject32

        def __set__(self, value):
            self._inject32 = value
            self.thisptr.injectX86(value)

    property inject64:
        def __get__(self):
            return self._inject64

        def __set__(self, value):
            self._inject64 = value
            self.thisptr.injectX64(value)

    property inject_func:
        def __get__(self):
            return self._inject_func

        def __set__(self, value):
            self._inject_func = value
            self.thisptr.injectFunction(value)

    property username:
        def __get__(self):
            return self._username

        def __set__(self, value):
            self._username = value
            self.thisptr.withLogin(self._username, self._password)

    property password:
        def __get__(self):
            return self._password

        def __set__(self, value):
            self._password = value
            self.thisptr.withLogin(self._username, self._password)

    property memory:
        def __get__(self):
            return self.thisptr.memory()

    property mle:
        def __get__(self):
            return self.thisptr.mle()

    property execution_time:
        def __get__(self):
            return self.thisptr.executionTime()

    property tle:
        def __get__(self):
            return self.thisptr.tle()

    property _handle:
        def __get__(self):
            return <unsigned long long>self.thisptr.process().get()


cpdef update_address_x86(unicode executable):
    JobbedProcessManager.updateAsmX86(executable)


cpdef update_address_x64(unicode executable):
    JobbedProcessManager.updateAsmX64(executable)
