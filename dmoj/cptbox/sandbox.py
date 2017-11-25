from __future__ import print_function

import errno
import logging
import os
import pty
import re
import select
import signal
import subprocess
import sys
import threading
import time

import six
from six.moves import range

from dmoj.cptbox._cptbox import *
from dmoj.cptbox.handlers import DISALLOW, _CALLBACK
from dmoj.cptbox.syscalls import translator, SYSCALL_COUNT, by_id
from dmoj.error import InternalError
from dmoj.utils.communicate import safe_communicate as _safe_communicate
from dmoj.utils.unicode import utf8text, utf8bytes

PIPE = object()
log = logging.getLogger('dmoj.cptbox')


def _find_exe(path):
    if os.path.isabs(path):
        return path
    if os.sep in path:
        return os.path.abspath(path)
    for dir in os.environ.get('PATH', os.defpath).split(os.pathsep):
        p = os.path.join(dir, path)
        if os.access(p, os.X_OK):
            return utf8bytes(p)
    raise OSError()


def file_info(path, split=re.compile(r'[\s,]').split):
    try:
        return split(utf8text(subprocess.check_output(['file', '-b', '-L', path])))
    except subprocess.CalledProcessError:
        return []


X86 = 'x86'
X64 = 'x64'
X32 = 'x32'
ARM = 'arm'


def file_arch(path):
    info = file_info(path)

    if '32-bit' in info:
        if 'ARM' in info:
            return ARM
        return X32 if 'x86-64' in info else X86
    elif '64-bit' in info:
        return X64
    return None


PYTHON_ARCH = file_arch(sys.executable)

_PIPE_BUF = getattr(select, 'PIPE_BUF', 512)
_SYSCALL_INDICIES = [None] * 5

if 'freebsd' in sys.platform:
    _SYSCALL_INDICIES[DEBUGGER_X64] = 4
else:
    _SYSCALL_INDICIES[DEBUGGER_X86] = 0
    _SYSCALL_INDICIES[DEBUGGER_X86_ON_X64] = 0
    _SYSCALL_INDICIES[DEBUGGER_X64] = 1
    _SYSCALL_INDICIES[DEBUGGER_X32] = 2
    _SYSCALL_INDICIES[DEBUGGER_ARM] = 3


def _eintr_retry_call(func, *args):
    while True:
        try:
            return func(*args)
        except (OSError, IOError) as e:
            if e.errno == errno.EINTR:
                continue
            raise


# (python arch, executable arch) -> debugger
_arch_map = {
    (X86, X86): DEBUGGER_X86,
    (X64, X64): DEBUGGER_X64,
    (X64, X86): DEBUGGER_X86_ON_X64,
    (X64, X32): DEBUGGER_X32,
    (X32, X32): DEBUGGER_X32,
    (X32, X86): DEBUGGER_X86_ON_X64,
    (ARM, ARM): DEBUGGER_ARM,
}


class AdvancedDebugger(Debugger):
    # Implements additional debugging functionality for convenience.

    def get_syscall_id(self, syscall):
        return translator[syscall][self._syscall_index]

    def readstr(self, address, max_size=4096):
        if self.address_bits == 32:
            address &= 0xFFFFFFFF
        try:
            return utf8text(super(AdvancedDebugger, self).readstr(address, max_size))
        except UnicodeDecodeError:
            # It's possible for the text to crash utf8text, but this would mean a
            # deliberate attack, so we kill the process here instead
            os.kill(self.pid, signal.SIGKILL)
            return ''


# SecurePopen is a subclass of a cython class, _cptbox.Process. Since it is exceedingly unwise
# to do everything in cython, determining the debugger class is left to do here. However, since
# the debugger is constructed in __cinit__, we have to pass the determined debugger class to
# SecurePopen.__new__. While we can simply override __new__, many complication arises from having
# different parameters to __new__ and __init__, the latter of which is given the *original* arguments
# as passed to type.__call__. Hence, we use a metaclass to pass the extra debugger argument to both
# __new__ and __init__.
class SecurePopenMeta(type):
    def __call__(self, argv, executable=None, *args, **kwargs):
        executable = executable or _find_exe(argv[0])
        arch = file_arch(executable)
        debugger = _arch_map.get((PYTHON_ARCH, arch))
        if debugger is None:
            raise RuntimeError('Executable type %s could not be debugged on Python type %s' % (arch, PYTHON_ARCH))
        return super(SecurePopenMeta, self).__call__(debugger, self.debugger_type, argv, executable, *args, **kwargs)


class SecurePopen(six.with_metaclass(SecurePopenMeta, Process)):
    debugger_type = AdvancedDebugger

    def __init__(self, debugger, _, args, executable=None, security=None, time=0, memory=0, stdin=PIPE, stdout=PIPE,
                 stderr=None, env=None, nproc=0, address_grace=4096, personality=0, cwd='',
                 fds=None, unbuffered=False, wall_time=None):
        self._debugger_type = debugger
        self._syscall_index = index = _SYSCALL_INDICIES[debugger]
        self._executable = executable or _find_exe(args[0])
        self._args = args
        self._chdir = cwd
        self._env = [utf8bytes('%s=%s' % i) for i in six.iteritems(env if env is not None else os.environ)]
        self._time = time
        self._wall_time = time * 3 if wall_time is None else wall_time
        self._cpu_time = time + 5 if time else 0
        self._memory = memory
        self._child_personality = personality
        self._child_memory = memory * 1024
        self._child_address = self._child_memory + address_grace * 1024 if memory else 0
        self._nproc = nproc
        self._tle = False
        self._fds = fds
        self.__init_streams(stdin, stdout, stderr, unbuffered)
        self.protection_fault = None

        self.debugger._syscall_index = index
        self.debugger.address_bits = 64 if debugger == DEBUGGER_X64 else 32

        self._security = security
        self._callbacks = [None] * MAX_SYSCALL_NUMBER
        if security is None:
            self._trace_syscalls = False
        else:
            for i in range(SYSCALL_COUNT):
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
        return self._memory and self.max_memory > self._memory

    @property
    def tle(self):
        return self._tle

    @property
    def r_execution_time(self):
        return self.wall_clock_time

    def kill(self):
        log.warning('Request the killing of process: %s', self.pid)
        print('Child is requested to be killed', file=sys.stderr)
        try:
            os.killpg(self.pid, signal.SIGKILL)
        except OSError:
            import traceback
            traceback.print_exc()

    def _callback(self, syscall):
        callback = self._callbacks[syscall]
        if callback is not None:
            return callback(self.debugger)
        return False

    def _protection_fault(self, syscall):
        # When signed, 0xFFFFFFFF is equal to -1, meaning that ptrace failed to read the syscall for some reason.
        # We can't continue debugging as this could potentially be unsafe, so we should exit loudly.
        # See <https://github.com/DMOJ/judge/issues/181> for more details.
        if syscall == 0xFFFFFFFF:
            raise InternalError('ptrace failed')
            # TODO: this would be more useful if we had access to a proper errno
            # import errno, os
            # err = ...
            # raise InternalError('ptrace error: %d (%s: %s)' % (err, errno.errorcode[err], os.strerror(err)))
        else:
            callname = 'unknown'
            index = self._syscall_index
            for id, call in enumerate(translator):
                if call[index] == syscall:
                    callname = by_id[id]
                    break

            self.protection_fault = (syscall, callname, [self.debugger.uarg0, self.debugger.uarg1,
                                                         self.debugger.uarg2, self.debugger.uarg3,
                                                         self.debugger.uarg4, self.debugger.uarg5])

    def _cpu_time_exceeded(self):
        log.warning('SIGXCPU in process %d', self.pid)
        print('SIGXCPU in child', file=sys.stderr)
        self._tle = True

    def _run_process(self):
        self._spawn(self._executable,
                    self._args,
                    self._env,
                    self._chdir,
                    self._fds)

        if self._child_stdin >= 0:
            os.close(self._child_stdin)
        if self._child_stdout >= 0:
            os.close(self._child_stdout)
        if self._child_stderr >= 0:
            os.close(self._child_stderr)
        self._started.set()
        code = self._monitor()

        if self._time and self.execution_time > self._time:
            self._tle = True
        self._died.set()

        return code

    def _shocker_thread(self):
        # On Linux, ignored signals still cause a notification under ptrace.
        # Hence, we use SIGWINCH, harmless and ignored signal to make wait4 return
        # pt_process::monitor, causing time to be updated.
        # On FreeBSD, a signal must not be ignored in order for wait4 to return.
        # Hence, we swallow SIGSTOP, which should never be used anyway, and use it
        # force an update.
        wake_signal = signal.SIGSTOP if 'freebsd' in sys.platform else signal.SIGWINCH
        self._started.wait()

        while not self._exited:
            if self.execution_time > self._time or self.wall_clock_time > self._wall_time:
                log.warning('Shocker activated and killed %d', self.pid)
                os.killpg(self.pid, signal.SIGKILL)
                self._tle = True
                break
            time.sleep(1)
            try:
                os.killpg(self.pid, wake_signal)
            except OSError:
                pass
            else:
                time.sleep(0.01)

    def __init_streams(self, stdin, stdout, stderr, unbuffered):
        self.stdin = self.stdout = self.stderr = None

        if unbuffered:
            master, slave = pty.openpty()

        if stdin is PIPE:
            self._child_stdin, self._stdin = (os.dup(slave), os.dup(master)) if unbuffered else os.pipe()
            self.stdin = os.fdopen(self._stdin, 'w')
        elif isinstance(stdin, int):
            self._child_stdin, self._stdin = stdin, -1
        elif stdin is not None:
            self._child_stdin, self._stdin = stdin.fileno(), -1
        else:
            self._child_stdin = self._stdin = -1

        if stdout is PIPE:
            self._stdout, self._child_stdout = (os.dup(master), os.dup(slave)) if unbuffered else os.pipe()
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

        if unbuffered:
            os.close(master)
            os.close(slave)

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

        stdout = None  # Return
        stderr = None  # Return
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
            except select.error as e:
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
            stdout = b''.join(stdout)
        if stderr is not None:
            stderr = b''.join(stderr)

        self.wait()
        return stdout, stderr

    safe_communicate = _safe_communicate


def can_debug(arch):
    return (PYTHON_ARCH, arch) in _arch_map
