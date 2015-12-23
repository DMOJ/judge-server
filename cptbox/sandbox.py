import os
import subprocess
import threading
import time
import select
import errno
import signal
import sys
import pty

import re

from _cptbox import *
from .syscalls import translator, SYSCALL_COUNT, by_id

DISALLOW = 0
ALLOW = 1
_CALLBACK = 2
STDOUTERR = 3

PIPE = object()


def _find_exe(path):
    if os.path.isabs(path):
        return path
    if os.sep in path:
        return os.path.abspath(path)
    for dir in os.environ.get('PATH', os.defpath).split(os.pathsep):
        p = os.path.join(dir, path)
        if os.access(p, os.X_OK):
            return p
    raise OSError()


def file_info(path, split=re.compile(r'[\s,]').split):
    try:
        return split(subprocess.check_output(['file', '-b', '-L', path]))
    except subprocess.CalledProcessError:
        return []


X86 = 'x86'
X64 = 'x64'
X32 = 'x32'


def file_arch(path):
    info = file_info(path)

    if '32-bit' in info:
        return X32 if 'x86-64' in info else X86
    elif '64-bit' in info:
        return X64
    return None

PYTHON_ARCH = file_arch(sys.executable)


_PIPE_BUF = getattr(select, 'PIPE_BUF', 512)
_SYSCALL_INDICIES = [None] * 3
_SYSCALL_INDICIES[DEBUGGER_X86] = 0
_SYSCALL_INDICIES[DEBUGGER_X86_ON_X64] = 0
_SYSCALL_INDICIES[DEBUGGER_X64] = 1


def _eintr_retry_call(func, *args):
    while True:
        try:
            return func(*args)
        except (OSError, IOError) as e:
            if e.errno == errno.EINTR:
                continue
            raise


class _SecurePopen(Process):
    def __init__(self, debugger, args, executable=None, security=None, time=0, memory=0, stdin=PIPE, stdout=PIPE,
                 stderr=None, env=None, nproc=0, address_grace=4096, cwd='', fds=None, unbuffered=False):
        self._debugger_type = debugger
        self._syscall_index = index = _SYSCALL_INDICIES[debugger]
        self._executable = executable or _find_exe(args[0])
        self._args = args
        self._chdir = cwd
        self._env = ['%s=%s' % i for i in (env if env is not None else os.environ).iteritems()]
        self._time = time
        self._cpu_time = time + 5
        self._memory = memory
        self._child_memory = memory * 1024
        self._child_address = self._child_memory + address_grace * 1024
        self._nproc = nproc
        self._tle = False
        self._fds = fds
        self.__init_streams(stdin, stdout, stderr, unbuffered)

        self._security = security
        self._callbacks = [None] * SYSCALL_COUNT
        if security is None:
            for i in xrange(SYSCALL_COUNT):
                self._handler(i, ALLOW)
        else:
            for i in xrange(SYSCALL_COUNT):
                handler = security.get(i, DISALLOW)
                call = translator[i][index]
                if call is None:
                    continue
                if not isinstance(handler, int):
                    if not callable(handler):
                        raise ValueError('Handler not callable: ' + handler)
                    self._callbacks[call] = handler
                    handler = _CALLBACK
                self._handler(call, handler)

        self._start_time = 0
        self._died_time = 0
        self._started = threading.Event()
        self._died = threading.Event()
        if time:
            # Spawn thread to kill process after it times out
            self._shocker = threading.Thread(target=self._shocker_thread)
            self._shocker.start()
        self._worker = threading.Thread(target=self._run_process)
        self._worker.start()

    def wait(self):
        self._died.wait()
        return self.returncode

    def poll(self):
        return self.returncode

    @property
    def mle(self):
        return self._memory is not None and self.max_memory > self._memory

    @property
    def tle(self):
        return self._tle

    @property
    def r_execution_time(self):
        return self._start_time and ((self._died_time or time.time()) - self._start_time)

    def kill(self):
        print>>sys.stderr, 'Child is requested to be killed'
        try:
            os.kill(self.pid, signal.SIGKILL)
        except OSError:
            import traceback
            traceback.print_exc()

    def _callback(self, syscall):
        callback = self._callbacks[syscall]
        if callback is not None:
            return callback(self.debugger)
        return False

    def _protection_fault(self, syscall):
        callname = None
        index = self._syscall_index
        for id, call in enumerate(translator):
            if call[index] == syscall:
                callname = by_id[id]
                break
        print>>sys.stderr, 'Protection fault on: %d (%s)' % (syscall, callname)
        print>>sys.stderr, 'Arg0: 0x%016x' % self.debugger.uarg0
        print>>sys.stderr, 'Arg1: 0x%016x' % self.debugger.uarg1
        print>>sys.stderr, 'Arg2: 0x%016x' % self.debugger.uarg2
        print>>sys.stderr, 'Arg3: 0x%016x' % self.debugger.uarg3
        print>>sys.stderr, 'Arg4: 0x%016x' % self.debugger.uarg4
        print>>sys.stderr, 'Arg5: 0x%016x' % self.debugger.uarg5

    def _cpu_time_exceeded(self):
        self._tle = True

    def _run_process(self):
        self._spawn(self._executable, self._args, self._env, self._chdir, self._fds)
        if self._child_stdin >= 0: os.close(self._child_stdin)
        if self._child_stdout >= 0: os.close(self._child_stdout)
        if self._child_stderr >= 0: os.close(self._child_stderr)
        self._started.set()
        self._start_time = time.time()
        code = self._monitor()

        self._died_time = time.time()
        if self._time and self.execution_time > self._time:
            self._tle = True
        self._died.set()
        return code

    def _shocker_thread(self):
        self._started.wait()

        while not self._exited:
            if self.execution_time > self._time:
                print>>sys.stderr, 'Shocker activated, ouch!'
                os.kill(self.pid, signal.SIGKILL)
                self._tle = True
                break
            time.sleep(1)
            try:
                os.kill(self.pid, signal.SIGWINCH)
            except OSError:
                pass
            else:
                time.sleep(0.01)

    def __init_streams(self, stdin, stdout, stderr, unbuffered):
        self.stdin = self.stdout = self.stderr = None
        
        if unbuffered:
            master, slave = pty.openpty()

        if stdin is PIPE:
            self._child_stdin, self._stdin = (slave, master) if unbuffered else os.pipe()
            self.stdin = os.fdopen(self._stdin, 'w')
        elif isinstance(stdin, int):
            self._child_stdin, self._stdin = stdin, -1
        elif stdin is not None:
            self._child_stdin, self._stdin = stdin.fileno(), -1
        else:
            self._child_stdin = self._stdin = -1

        if stdout is PIPE:
            self._stdout, self._child_stdout = (master, slave) if unbuffered else os.pipe()
            self.stdout = os.fdopen(self._stdout, 'r')
        elif isinstance(stdout, int):
            self._stdout, self._child_stdout = -1, stdout
        elif stdout is not None:
            self._stdout, self._child_stdout = -1, stdout.fileno()
        else:
            self._stdout = self._child_stdout = -1

        if stderr is PIPE:
            self._stderr, self._child_stderr = os.pipe()
            self.stderr = os.fdopen(self._stderr, 'r')
        elif isinstance(stderr, int):
            self._stderr, self._child_stderr = -1, stderr
        elif stderr is not None:
            self._stderr, self._child_stderr = -1, stderr.fileno()
        else:
            self._stderr = self._child_stderr = -1

    # All communicate stuff copied from subprocess.
    def communicate(self, input=None):
        # Optimization: If we are only using one pipe, or no pipe at
        # all, using select() or threads is unnecessary.
        if [self.stdin, self.stdout, self.stderr].count(None) >= 2:
            stdout = None
            stderr = None
            if self.stdin:
                if input:
                    try:
                        self.stdin.write(input)
                    except IOError as e:
                        if e.errno != errno.EPIPE and e.errno != errno.EINVAL:
                            raise
                self.stdin.close()
            elif self.stdout:
                stdout = _eintr_retry_call(self.stdout.read)
                self.stdout.close()
            elif self.stderr:
                stderr = _eintr_retry_call(self.stderr.read)
                self.stderr.close()
            self.wait()
            return (stdout, stderr)

        return self._communicate(input)

    def _communicate(self, input):
        if self.stdin:
            # Flush stdio buffer.  This might block, if the user has
            # been writing to .stdin in an uncontrolled fashion.
            self.stdin.flush()
            if not input:
                self.stdin.close()

        stdout = None # Return
        stderr = None # Return
        fd2file = {}
        fd2output = {}

        poller = select.poll()

        def register_and_append(file_obj, eventmask):
            poller.register(file_obj.fileno(), eventmask)
            fd2file[file_obj.fileno()] = file_obj

        def close_unregister_and_remove(fd):
            poller.unregister(fd)
            fd2file[fd].close()
            fd2file.pop(fd)

        if self.stdin and input:
            register_and_append(self.stdin, select.POLLOUT)

        select_POLLIN_POLLPRI = select.POLLIN | select.POLLPRI
        if self.stdout:
            register_and_append(self.stdout, select_POLLIN_POLLPRI)
            fd2output[self.stdout.fileno()] = stdout = []
        if self.stderr:
            register_and_append(self.stderr, select_POLLIN_POLLPRI)
            fd2output[self.stderr.fileno()] = stderr = []

        input_offset = 0
        while fd2file:
            try:
                ready = poller.poll()
            except select.error, e:
                if e.args[0] == errno.EINTR:
                    continue
                raise

            for fd, mode in ready:
                if mode & select.POLLOUT:
                    chunk = input[input_offset:input_offset + _PIPE_BUF]
                    try:
                        input_offset += os.write(fd, chunk)
                    except OSError as e:
                        if e.errno == errno.EPIPE:
                            close_unregister_and_remove(fd)
                        else:
                            raise
                    else:
                        if input_offset >= len(input):
                            close_unregister_and_remove(fd)
                elif mode & select_POLLIN_POLLPRI:
                    data = os.read(fd, 4096)
                    if not data:
                        close_unregister_and_remove(fd)
                    fd2output[fd].append(data)
                else:
                    # Ignore hang up or errors.
                    close_unregister_and_remove(fd)

        # All data exchanged.  Translate lists into strings.
        if stdout is not None:
            stdout = ''.join(stdout)
        if stderr is not None:
            stderr = ''.join(stderr)

        self.wait()
        return stdout, stderr


# (python arch, executable arch) -> debugger
_arch_map = {
    (X86, X86): DEBUGGER_X86,
    (X64, X64): DEBUGGER_X64,
    (X64, X86): DEBUGGER_X86_ON_X64,
}


def SecurePopen(argv, executable=None, *args, **kwargs):
    executable = executable or _find_exe(argv[0])
    arch = file_arch(executable)
    debugger = _arch_map.get((PYTHON_ARCH, arch))
    if debugger is None:
        raise RuntimeError('Executable type %s could not be debugged on Python type %s' % (arch, PYTHON_ARCH))
    return _SecurePopen(debugger, argv, executable, *args, **kwargs)
