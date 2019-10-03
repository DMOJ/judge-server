import logging
import os
import select
import signal
import subprocess
import sys
import threading
import time
from typing import List, Optional

from dmoj.cptbox._cptbox import *
from dmoj.cptbox.handlers import ALLOW, DISALLOW, _CALLBACK
from dmoj.cptbox.syscalls import SYSCALL_COUNT, by_id, translator
from dmoj.error import InternalError
from dmoj.utils.communicate import safe_communicate as _safe_communicate
from dmoj.utils.os_ext import (
    ARCH_A64, ARCH_ARM, ARCH_X32, ARCH_X64, ARCH_X86, INTERPRETER_ARCH, file_arch, find_exe_in_path,
)
from dmoj.utils.unicode import utf8bytes, utf8text

PIPE = subprocess.PIPE
log = logging.getLogger('dmoj.cptbox')

_PIPE_BUF = getattr(select, 'PIPE_BUF', 512)
_SYSCALL_INDICIES: List[Optional[int]] = [None] * 7

if 'freebsd' in sys.platform:
    _SYSCALL_INDICIES[DEBUGGER_X64] = 4
else:
    _SYSCALL_INDICIES[DEBUGGER_X86] = 0
    _SYSCALL_INDICIES[DEBUGGER_X86_ON_X64] = 0
    _SYSCALL_INDICIES[DEBUGGER_X64] = 1
    _SYSCALL_INDICIES[DEBUGGER_X32] = 2
    _SYSCALL_INDICIES[DEBUGGER_ARM] = 3
    _SYSCALL_INDICIES[DEBUGGER_ARM64] = 5

# (python arch, executable arch) -> debugger
_arch_map = {
    (ARCH_X86, ARCH_X86): DEBUGGER_X86,
    (ARCH_X64, ARCH_X64): DEBUGGER_X64,
    (ARCH_X64, ARCH_X86): DEBUGGER_X86_ON_X64,
    (ARCH_X64, ARCH_X32): DEBUGGER_X32,
    (ARCH_X32, ARCH_X32): DEBUGGER_X32,
    (ARCH_X32, ARCH_X86): DEBUGGER_X86_ON_X64,
    (ARCH_ARM, ARCH_ARM): DEBUGGER_ARM,
    (ARCH_A64, ARCH_ARM): DEBUGGER_ARM,
    (ARCH_A64, ARCH_A64): DEBUGGER_ARM64,
}


class AdvancedDebugger(Debugger):
    # Implements additional debugging functionality for convenience.

    @property
    def syscall_name(self):
        return self.get_syscall_name(self.syscall)

    def get_syscall_name(self, syscall):
        callname = 'unknown'
        index = self._syscall_index
        for id, call in enumerate(translator):
            if syscall in call[index]:
                callname = by_id[id]
                break
        return callname

    def readstr(self, address, max_size=4096):
        if self.address_bits == 32:
            address &= 0xFFFFFFFF
        try:
            return utf8text(super().readstr(address, max_size))
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
class TracedPopenMeta(type):
    def __call__(self, argv, executable=None, *args, **kwargs):
        executable = executable or find_exe_in_path(argv[0])
        arch = file_arch(executable)
        debugger = _arch_map.get((INTERPRETER_ARCH, arch))
        if debugger is None:
            raise RuntimeError('Executable type %s could not be debugged on Python type %s' % (arch, INTERPRETER_ARCH))
        return super().__call__(debugger, self.debugger_type, argv, executable, *args, **kwargs)


class TracedPopen(Process, metaclass=TracedPopenMeta):
    debugger_type = AdvancedDebugger

    def __init__(self, debugger, _, args, executable=None, security=None, time=0, memory=0, stdin=PIPE, stdout=PIPE,
                 stderr=None, env=None, nproc=0, fsize=0, address_grace=4096, data_grace=0, personality=0, cwd='',
                 fds=None, wall_time=None):
        self._debugger_type = debugger
        self._syscall_index = index = _SYSCALL_INDICIES[debugger]
        self._executable = executable or find_exe_in_path(args[0])
        self._args = args
        self._chdir = cwd
        self._env = [utf8bytes('%s=%s' % (arg, val))
                     for arg, val in (env if env is not None else os.environ).items() if val is not None]
        self._time = time
        self._wall_time = time * 3 if wall_time is None else wall_time
        self._cpu_time = time + 5 if time else 0
        self._memory = memory
        self._child_personality = personality
        self._child_memory = memory * 1024 + data_grace * 1024
        self._child_address = memory * 1024 + address_grace * 1024 if memory else 0
        self._nproc = nproc
        self._fsize = fsize
        self._tle = False
        self._fds = fds
        self.__init_streams(stdin, stdout, stderr)
        self.protection_fault = None

        self.debugger._syscall_index = index
        self.debugger.address_bits = 64 if debugger in (DEBUGGER_X64, DEBUGGER_ARM64) else 32

        self._security = security
        self._callbacks = [None] * MAX_SYSCALL_NUMBER
        self._syscall_whitelist = [False] * MAX_SYSCALL_NUMBER
        if security is None:
            self._trace_syscalls = False
        else:
            for i in range(SYSCALL_COUNT):
                handler = security.get(i, DISALLOW)
                for call in translator[i][index]:
                    if call is None:
                        continue
                    if isinstance(handler, int):
                        self._syscall_whitelist[call] = handler == ALLOW
                    else:
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
        if not self.was_initialized:
            if self.returncode == 203:
                raise RuntimeError('failed to set up seccomp policy')
            elif self.returncode == 204:
                raise RuntimeError('failed to ptrace child, check Yama config '
                                   '(https://www.kernel.org/doc/Documentation/security/Yama.txt, should be '
                                   'at most 1); if running in Docker, must run container with `--privileged`')
        return self.returncode

    def poll(self):
        return self.returncode

    @property
    def mle(self):
        return self._memory and self.max_memory > self._memory

    @property
    def tle(self):
        return self._tle

    def kill(self):
        log.warning('Request the killing of process: %s', self.pid)
        try:
            os.killpg(self.pid, signal.SIGKILL)
        except OSError:
            import traceback
            traceback.print_exc()

    def _callback(self, syscall):
        try:
            callback = self._callbacks[syscall]
        except IndexError:
            if self._syscall_index == 3:
                # ARM-specific
                return 0xf0000 < syscall < 0xf0006
            return False

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
            callname = self.debugger.get_syscall_name(syscall)
            self.protection_fault = (syscall, callname, [self.debugger.uarg0, self.debugger.uarg1,
                                                         self.debugger.uarg2, self.debugger.uarg3,
                                                         self.debugger.uarg4, self.debugger.uarg5])

    def _cpu_time_exceeded(self):
        log.warning('SIGXCPU in process %d', self.pid)
        self._tle = True

    def _run_process(self):
        self._spawn(self._executable,
                    self._args,
                    self._env,
                    self._chdir,
                    self._fds)

        if self.stdin_needs_close:
            os.close(self._child_stdin)
        if self.stdout_needs_close:
            os.close(self._child_stdout)
        if self.stderr_needs_close:
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

    def __init_streams(self, stdin, stdout, stderr):
        self.stdin = self.stdout = self.stderr = None
        self.stdin_needs_close = self.stdout_needs_close = self.stderr_needs_close = False

        if stdin == PIPE:
            self._child_stdin, self._stdin = os.pipe()
            self.stdin = os.fdopen(self._stdin, 'wb')
            self.stdin_needs_close = True
        elif isinstance(stdin, int):
            self._child_stdin, self._stdin = stdin, -1
        elif stdin is not None:
            self._child_stdin, self._stdin = stdin.fileno(), -1
        else:
            self._child_stdin = self._stdin = -1

        if stdout == PIPE:
            self._stdout, self._child_stdout = os.pipe()
            self.stdout = os.fdopen(self._stdout, 'rb')
            self.stdout_needs_close = True
        elif isinstance(stdout, int):
            self._stdout, self._child_stdout = -1, stdout
        elif stdout is not None:
            self._stdout, self._child_stdout = -1, stdout.fileno()
        else:
            self._stdout = self._child_stdout = -1

        if stderr == PIPE:
            self._stderr, self._child_stderr = os.pipe()
            self.stderr = os.fdopen(self._stderr, 'rb')
            self.stderr_needs_close = True
        elif isinstance(stderr, int):
            self._stderr, self._child_stderr = -1, stderr
        elif stderr is not None:
            self._stderr, self._child_stderr = -1, stderr.fileno()
        else:
            self._stderr = self._child_stderr = -1

    communicate = _safe_communicate

    def unsafe_communicate(self, input=None):
        return _safe_communicate(self, input=input, outlimit=sys.maxsize, errlimit=sys.maxsize)


def can_debug(arch):
    return (INTERPRETER_ARCH, arch) in _arch_map
