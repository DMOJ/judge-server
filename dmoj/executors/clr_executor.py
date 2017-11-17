from __future__ import print_function

import os
import re
import subprocess
import msvcrt
from threading import Thread
import time
import sys

import six

from dmoj.utils.communicate import safe_communicate
from dmoj.executors.base_executor import CompiledExecutor
from dmoj.judgeenv import env
from dmoj.utils.winutils import execution_time, max_memory
from dmoj.utils.pywinjob import *

reexc = re.compile(r'E1AE1B1F-C5FE-4335-B642-9446634350A0:\r?\n(.*?):')


class CLRProcess(object):
    csbox = env.runtime.csbox or os.path.join(os.path.dirname(__file__), 'csbox.exe')

    if not isinstance(csbox, six.text_type):
        csbox = csbox.decode('mbcs')

    def __init__(self, executable, dir, time, memory):
        self._process = None
        self._job = None
        self._port = None

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
        if self._job is not None:
            CloseHandle(self._job)
        if self._port is not None:
            CloseHandle(self._port)

    def _monitor(self):
        code = DWORD()
        key = c_void_p()
        overlapped = OVERLAPPED()
        while GetQueuedCompletionStatus(self._port, byref(code), byref(key), byref(overlapped), INFINITE):
            if key.value == self._job:
                if code.value == JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO:
                    break
                elif code.value == JOB_OBJECT_MSG_JOB_MEMORY_LIMIT:
                    self.mle = True
                    TerminateProcess(self._process, 0xDEADBEEF)
                    WaitForSingleObject(self._process, INFINITE)
                    break
        else:
            raise WinError()

    def _shocker(self):
        time.sleep(self.time_limit)
        if WaitForSingleObject(self._process, 0) == WAIT_TIMEOUT:
            print('Ouch, shocker activated!', file=sys.stderr)
            TerminateProcess(self._process, 0xDEADBEEF)
            WaitForSingleObject(self._process, INFINITE)

    def _execute(self, args, cwd):
        args = subprocess.list2cmdline(args)
        if not isinstance(args, six.text_type):
            args = args.decode('mbcs')

        if not isinstance(cwd, six.text_type):
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

        self._port = CreateIoCompletionPort(INVALID_HANDLE_VALUE, None, 0, 1)
        if not self._port:
            raise WinError()

        if not SetInformationJobObject(job, JobObjectExtendedLimitInformation, byref(limits),
                                       sizeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)):
            raise WinError()

        port = JOBOBJECT_ASSOCIATE_COMPLETION_PORT()
        port.CompletionKey = job
        port.CompletionPort = self._port
        if not SetInformationJobObject(job, JobObjectAssociateCompletionPortInformation, byref(port),
                                       sizeof(JOBOBJECT_ASSOCIATE_COMPLETION_PORT)):
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
                             None, cwd, byref(si), byref(pi)):
            raise WinError()

        if AssignProcessToJobObject(job, pi.hProcess) == 0:
            raise WinError()

        self._monitor_thread = Thread(target=self._monitor)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

        if ResumeThread(pi.hThread) == -1:
            raise WinError()

        if not CloseHandle(pi.hThread):
            raise WinError()

        self._process = pi.hProcess
        self.stdin = os.fdopen(msvcrt.open_osfhandle(stdin, 0), 'wb')
        self.stdout = os.fdopen(msvcrt.open_osfhandle(stdout, 0), 'rb')
        self.stderr = os.fdopen(msvcrt.open_osfhandle(stderr, 0), 'rb')

        if not CloseHandle(stdin_):
            raise WinError()
        if not CloseHandle(stdout_):
            raise WinError()
        if not CloseHandle(stderr_):
            raise WinError()

        self._shocker_thread = Thread(target=self._shocker)
        self._shocker_thread.daemon = True
        self._shocker_thread.start()

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
        self.tle |= self.execution_time > self.time_limit
        self.max_memory = max_memory(self._process) / 1024.
        self.mle |= self.max_memory > self.memory_limit

    def _find_exception(self, stderr):
        if len(stderr) < 8192:
            match = reexc.search(stderr)
            return match and match.group(1)

    # TODO: avoid hijacking private methods and stealing their guts.
    _communicate = subprocess.Popen._communicate.im_func
    _readerthread = subprocess.Popen._readerthread.im_func
    # Duck-typing: this is only to appear like a Popen to fool Popen's guts.
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


class CLRExecutor(CompiledExecutor):
    compiler = None
    compile_args = ['-nologo', '-out:{exe}', '{source}']

    @classmethod
    def get_command(cls):
        return cls.runtime_dict.get(cls.compiler)

    def get_compile_args(self):
        return [self.runtime_dict[self.compiler]] + [arg.format(exe=self.get_compiled_file() +
                                                                    self.get_executable_ext(),
                                                                source=self._code)
                                                     for arg in self.compile_args]

    def launch(self, *args, **kwargs):
        return CLRProcess(self.get_executable(), self._dir, kwargs.get('time'), kwargs.get('memory'))

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen(self.get_cmdline() + list(args), cwd=self._dir,
                                executable=self.get_executable(), **kwargs)

    @classmethod
    def get_compiler_basename(cls):
        return '%s.exe' % cls.compiler

    @classmethod
    def get_find_first_mapping(cls):
        versions = ['v4.0.30319', 'v3.5', 'v3.0', 'v2.0.50727']
        return {cls.compiler: [
            os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Microsoft.NET', 'Framework',
                         version, cls.get_compiler_basename()) for version in versions]}

    @classmethod
    def get_version_flags(cls, command):
        return ['/?']
