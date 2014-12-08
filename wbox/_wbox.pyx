from os import fdopen, O_RDONLY, O_WRONLY
from msvcrt import open_osfhandle

from libc.stdint cimport uint32_t

ctypedef const Py_UNICODE *LPCWSTR
ctypedef Py_UNICODE *LPWSTR
ctypedef void *HANDLE
ctypedef uint32_t DWORD


cdef extern from 'windows.h' nogil:
    DWORD WaitForSingleObject(HANDLE, DWORD milliseconds)
    cdef DWORD INFINITE
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
        JobbedProcessManager()

        bint spawn()
        bint terminate(unsigned code)

        JobbedProcessManager &time(double seconds)
        JobbedProcessManager &memory(size_t bytes)
        JobbedProcessManager &processes(int count)
        JobbedProcessManager &withLogin(LPCWSTR username, LPCWSTR password);
        JobbedProcessManager &command(LPCWSTR cmdline);
        JobbedProcessManager &executable(LPCWSTR executable)
        JobbedProcessManager &directory(LPCWSTR directory)

        AutoHandle &process()
        AutoHandle &job()
        AutoHandle &stdIn()
        AutoHandle &stdOut()
        AutoHandle &stdErr()


cdef class UserManager:
    cdef CUserManager *thisptr

    def __cinit__(self, username=None, password=None):
        if username is not None:
            self.thisptr = new CUserManager(username)
        elif username is not None and password is not None:
            self.thisptr = new CUserManager(username, password)
        else:
            self.thisptr = new CUserManager()

    def __dealloc__(self):
        del self.thisptr

    property username:
        def __get__(self):
            return self.thisptr.username()

    property password:
        def __get__(self):
            return self.thisptr.password()


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
    cdef object _stdin, _stdout, _stderr

    def __cinit__(self, username, password):
        self.thisptr = new JobbedProcessManager()
        self._time_limit = 0
        self._memory_limit = 0
        self._process_limit = 0
        self._username = username
        self._password = password
        self._executable = self._dir = u''
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
        time = timeout or INFINITE
        with nogil:
            result = WaitForSingleObject(self.thisptr.process().get(), time)
        return result

    def get_exit_code(self):
        cdef DWORD code
        if not GetExitCodeProcess(self.thisptr.process().get(), &code):
            raise WindowsError()
        return None if code == 259 else code

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