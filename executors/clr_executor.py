import os
import re
import ctypes
import subprocess
import msvcrt

from communicate import safe_communicate
from error import CompileError
from executors.resource_proxy import ResourceProxy
from judgeenv import env
from winutils import execution_time, max_memory
from pywinjob import *


reexc = re.compile(r'E1AE1B1F-C5FE-4335-B642-9446634350A0:\r?\n(.*?):')


class CLRProcess(object):
    csbox = os.path.join(os.path.dirname(__file__), 'csbox.exe')
    if not isinstance(csbox, unicode):
        csbox = csbox.decode('mbcs')

    def __init__(self, executable, dir, time, memory):
        self._process = None
        self._job = None

        self.time_limit = time
        self.memory_limit = memory
        self.tle = False
        self.execution_time = None
        self.mle = False
        self.max_memory = None
        self.feedback = None
        self.returncode = None
        self._execute([self.csbox, dir, executable], dir)

    def __del__(self):
        if self._process is not None:
            CloseHandle(self._process)
            CloseHandle(self._job)

    def _execute(self, args, cwd):
        args = subprocess.list2cmdline(args)
        if not isinstance(args, unicode):
            args = args.decode('mbcs')

        if not isinstance(cwd, unicode):
            cwd = cwd.decode('mbcs')

        limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.JobMemoryLimit = self.memory_limit * 1024  # bytes
        limits.BasicLimitInformation.PerJobUserTimeLimit = int(self.time_limit * 10000000)  # 100ns units
        limits.BasicLimitInformation.LimitFlags = (JOB_OBJECT_LIMIT_ACTIVE_PROCESS |
                                                   JOB_OBJECT_LIMIT_JOB_MEMORY |
                                                   JOB_OBJECT_LIMIT_JOB_TIME)
        limits.BasicLimitInformation.ActiveProcessLimit = 1

        self._job = job = CreateJobObject(None, None)
        if not job:
            raise WinError()

        if not SetInformationJobObject(job, JobObjectExtendedLimitInformation, ctypes.byref(limits),
                                       ctypes.sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)):
            raise WinError()

        stdin_, stdin = CreatePipe()
        stdout, stdout_ = CreatePipe()
        stderr, stderr_ = CreatePipe()
        stdin_ = make_inheritable(stdin_)
        stdout_ = make_inheritable(stdout_)
        stderr_ = make_inheritable(stderr_)

        si = STARTUPINFO()
        si.cb = sizeof(STARTUPINFO)
        si.dwFlags = STARTF_USESTDHANDLES
        si.hStdInput = stdin_
        si.hStdOutput = stdout_
        si.hStdError = stderr_

        pi = PROCESS_INFORMATION()

        if not CreateProcess(self.csbox, args, None, None, True, CREATE_SUSPENDED | CREATE_BREAKAWAY_FROM_JOB,
                             None, cwd, ctypes.byref(si), ctypes.byref(pi)):
            raise WinError()

        if AssignProcessToJobObject(job, pi.hProcess) == 0:
            raise WinError()

        if ResumeThread(pi.hThread) == -1:
            raise WinError()

        if not CloseHandle(pi.hThread):
            raise WinError()

        self._process = pi.hProcess
        self.stdin = os.fdopen(msvcrt.open_osfhandle(stdin, 0), 'wb')
        self.stdout = os.fdopen(msvcrt.open_osfhandle(stdout, 0), 'rb')
        self.stderr = os.fdopen(msvcrt.open_osfhandle(stderr, 0), 'rb')

        if not CloseHandle(stdin_):  raise WinError()
        if not CloseHandle(stdout_): raise WinError()
        if not CloseHandle(stderr_): raise WinError()

    def wait(self):
        wait = WaitForSingleObject(self._process, int(self.time_limit * 1000))
        if wait != WAIT_OBJECT_0:
            # Warning: this doesn't protect .communicate() from hanging because the fd is open
            self.tle |= True
            if not TerminateProcess(self._process, 0xDEADBEEF):
                raise WinError()
            WaitForSingleObject(self._process, INFINITE)
        return self.poll()

    def poll(self):
        if self.returncode is None:
            self.returncode = GetExitCodeProcess(self._process)
        return self.returncode

    @property
    def r_execution_time(self):
        return self.execution_time

    def _update_stats(self):
        self.execution_time = execution_time(self._process)
        self.tie = self.execution_time > self.time_limit
        self.max_memory = max_memory(self._process) / 1024.
        self.mle = self.max_memory > self.memory_limit

    def _find_exception(self, stderr):
        if len(stderr) < 8192:
            match = reexc.search(stderr)
            return match and match.group(1)

    _communicate = subprocess.Popen._communicate.im_func
    _readerthread = subprocess.Popen._readerthread.im_func
    universal_newlines = False

    def communicate(self, stdin=None):
        try:
            stdout, stderr = self._communicate(stdin)
            self.feedback = self._find_exception(stderr)
            return stdout, stderr
        finally:
            self._update_stats()

    def safe_communicate(self, stdin=None, outlimit=None, errlimit=None):
        try:
            stdout, stderr = safe_communicate(self, stdin, outlimit, errlimit)
            self.feedback = self._find_exception(stderr)
            return stdout, stderr
        finally:
            self._update_stats()


class CLRExecutor(ResourceProxy):
    extension = None
    compiler = None

    def __init__(self, problem_id, source_code):
        super(CLRExecutor, self).__init__()
        source_code_file = self._file('%s.%s' % (problem_id, self.extension))
        self.name = self._file('%s.exe' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

        csc_args = [env['runtime'][self.compiler], '-nologo', '-out:%s' % self.name, source_code_file]

        csc_process = subprocess.Popen(csc_args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, cwd=self._dir)
        compile_error, _ = csc_process.communicate()
        if csc_process.returncode != 0:
            raise CompileError(compile_error)
        self.warning = compile_error

    def launch(self, *args, **kwargs):
        return CLRProcess(self.name, self._dir, kwargs.get('time'), kwargs.get('memory'))

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen([self.name] + list(args), cwd=self._dir, **kwargs)