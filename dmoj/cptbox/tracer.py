import errno
import logging
import os
import select
import signal
import subprocess
import sys
import threading
from typing import Callable, List, Mapping, Optional, Tuple, Type

from dmoj.cptbox._cptbox import *
from dmoj.cptbox.handlers import ALLOW, DISALLOW, ErrnoHandlerCallback, _CALLBACK
from dmoj.cptbox.syscalls import SYSCALL_COUNT, by_id, sys_execve, sys_exit, sys_exit_group, sys_getpid, translator
from dmoj.utils.communicate import safe_communicate as _safe_communicate
from dmoj.utils.os_ext import OOM_SCORE_ADJ_MAX, oom_score_adj
from dmoj.utils.unicode import utf8bytes, utf8text

PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT
log = logging.getLogger('dmoj.cptbox')

_PIPE_BUF = getattr(select, 'PIPE_BUF', 512)
_SYSCALL_INDICIES: List[Optional[int]] = [None] * PTBOX_ABI_COUNT

_SYSCALL_INDICIES[PTBOX_ABI_X86] = 0
_SYSCALL_INDICIES[PTBOX_ABI_X64] = 1
_SYSCALL_INDICIES[PTBOX_ABI_X32] = 2
_SYSCALL_INDICIES[PTBOX_ABI_ARM] = 3
_SYSCALL_INDICIES[PTBOX_ABI_FREEBSD_X64] = 4
_SYSCALL_INDICIES[PTBOX_ABI_ARM64] = 5

FREEBSD = sys.platform.startswith('freebsd')
BAD_SECCOMP = sys.platform == 'linux' and tuple(map(int, os.uname().release.partition('-')[0].split('.'))) < (4, 8)

_address_bits = {
    PTBOX_ABI_X86: 32,
    PTBOX_ABI_X64: 64,
    PTBOX_ABI_X32: 32,
    PTBOX_ABI_ARM: 32,
    PTBOX_ABI_ARM64: 64,
    PTBOX_ABI_FREEBSD_X64: 64,
}

HandlerCallback = Callable[[Debugger], bool]


class MaxLengthExceeded(ValueError):
    pass


class AdvancedDebugger(Debugger):
    # Implements additional debugging functionality for convenience.

    @property
    def syscall_name(self):
        return self.get_syscall_name(self.syscall)

    @property
    def address_bits(self):
        return _address_bits.get(self.abi)

    @property
    def noop_syscall_id(self):
        if self.abi == PTBOX_ABI_INVALID:
            raise ValueError('ABI is invalid')
        return translator[sys_getpid][_SYSCALL_INDICIES[self.abi]][0]

    def get_syscall_name(self, syscall):
        if self.abi == PTBOX_ABI_INVALID:
            return 'failed to read registers'
        callname = 'unknown'
        index = _SYSCALL_INDICIES[self.abi]
        for id, call in enumerate(translator):
            if syscall in call[index]:
                callname = by_id[id]
                break
        return callname

    def readstr(self, address, max_size=4096):
        if self.address_bits == 32:
            address &= 0xFFFFFFFF
        read = super().readstr(address, max_size + 1)
        if read is None:
            return None
        if len(read) > max_size:
            raise MaxLengthExceeded(read)
        return utf8text(read)


class TracedPopen(Process):
    _executable: bytes
    _last_ptrace_errno: Optional[int]
    _spawn_error: Optional[Type[BaseException]]

    debugger: AdvancedDebugger
    protection_fault: Optional[Tuple[int, str, List[int], Optional[int]]]

    def __init__(
        self,
        args: List[bytes],
        *,
        executable: bytes,
        security=None,
        time: int = 0,
        memory: int = 0,
        stdin: Optional[int] = PIPE,
        stdout: Optional[int] = PIPE,
        stderr: Optional[int] = None,
        env: Optional[Mapping[str, Optional[str]]] = None,
        nproc: int = 0,
        fsize: int = 0,
        address_grace: int = 4096,
        data_grace: int = 0,
        personality: int = 0,
        cwd: bytes = b'',
        wall_time: Optional[float] = None,
        cpu_affinity: Optional[List[int]] = None,
    ) -> None:
        self._executable = executable

        if BAD_SECCOMP:
            raise RuntimeError(f'Sandbox requires Linux 4.8+ to use seccomp, you have {os.uname().release}')

        self._args = args
        self._chdir = cwd
        self._env = [
            utf8bytes(f'{arg}={val}')
            for arg, val in (env if env is not None else os.environ).items()
            if val is not None
        ]
        self._time = time
        self._wall_time = time * 3 if wall_time is None else wall_time
        self._cpu_time = time + 5 if time else 0
        self._memory = memory
        self._child_personality = personality
        self._child_memory = memory * 1024 + data_grace * 1024 if memory else 0
        self._child_address = memory * 1024 + address_grace * 1024 if memory else 0
        self._nproc = nproc
        self._fsize = fsize

        if cpu_affinity:
            for cpu in cpu_affinity:
                self._cpu_affinity_mask |= 1 << cpu

        self._is_tle = False
        self._is_ole = False
        self.__init_streams(stdin, stdout, stderr)
        self._last_ptrace_errno = None
        self.protection_fault = None

        self._security = security
        self._callbacks = [[None] * MAX_SYSCALL_NUMBER for _ in range(PTBOX_ABI_COUNT)]
        if security is None:
            self._trace_syscalls = False
        else:
            for abi in SUPPORTED_ABIS:
                index = _SYSCALL_INDICIES[abi]
                assert index is not None
                for i in range(SYSCALL_COUNT):
                    for call in translator[i][index]:
                        if call is None:
                            continue
                        handler = security.get(i, DISALLOW)
                        if not isinstance(handler, int):
                            if not callable(handler):
                                raise ValueError('Handler not callable: ' + handler)
                            self._callbacks[abi][call] = handler
                            handler = _CALLBACK
                        self._handler(abi, call, handler)

        self._died = threading.Event()
        self._spawned_or_errored = threading.Event()
        self._spawn_error = None

        if time:
            # Spawn thread to kill process after it times out
            self._shocker = threading.Thread(target=self._shocker_thread)
            self._shocker.start()
        self._worker = threading.Thread(target=self._run_process)
        self._worker.start()

        self._spawned_or_errored.wait()
        if self._spawn_error:
            raise self._spawn_error

    def create_debugger(self) -> AdvancedDebugger:
        return AdvancedDebugger(self)

    def _get_seccomp_handlers(self) -> List[int]:
        handlers = [-1] * MAX_SYSCALL_NUMBER
        index = _SYSCALL_INDICIES[NATIVE_ABI]
        assert index is not None
        for i in range(SYSCALL_COUNT):
            # Ensure at least one syscall traps, including the execve so we know the process started.
            # Otherwise, a simple assembly program could terminate without ever trapping.
            if i in (sys_execve, sys_exit, sys_exit_group):
                continue
            handler = self._security.get(i, DISALLOW)
            for call in translator[i][index]:
                if call is None:
                    continue
                if isinstance(handler, int) and handler == ALLOW:
                    handlers[call] = 0
                elif isinstance(handler, ErrnoHandlerCallback):
                    handlers[call] = handler.errno
        return handlers

    def wait(self) -> int:
        self._died.wait()
        assert self.returncode is not None
        if not self.was_initialized:
            if self.returncode == PTBOX_SPAWN_FAIL_NO_NEW_PRIVS:
                raise RuntimeError('failed to call prctl(PR_SET_NO_NEW_PRIVS)')
            elif self.returncode == PTBOX_SPAWN_FAIL_SECCOMP:
                raise RuntimeError('failed to set up seccomp policy')
            elif self.returncode == PTBOX_SPAWN_FAIL_TRACEME:
                raise RuntimeError(
                    'failed to ptrace child, check Yama config '
                    '(https://www.kernel.org/doc/Documentation/security/Yama.txt, should be '
                    'at most 1); if running in Docker, must run container with `--cap-add=SYS_PTRACE`'
                )
            elif self.returncode == PTBOX_SPAWN_FAIL_EXECVE:
                raise RuntimeError('failed to spawn child')
            elif self.returncode == PTBOX_SPAWN_FAIL_SETAFFINITY:
                raise RuntimeError('failed to set child affinity')
            elif self.returncode >= 0:
                raise RuntimeError('process failed to initialize with unknown exit code: %d' % self.returncode)
        return self.returncode

    def poll(self) -> Optional[int]:
        return self.returncode

    def mark_ole(self) -> None:
        self._is_ole = True

    @property
    def is_ir(self) -> bool:
        assert self.returncode is not None
        return self.returncode > 0

    @property
    def is_mle(self) -> bool:
        return self._memory != 0 and self.max_memory > self._memory

    @property
    def is_ole(self) -> bool:
        return self._is_ole

    @property
    def is_rte(self) -> bool:
        return self.returncode is None or self.returncode < 0  # Killed by signal

    @property
    def is_tle(self) -> bool:
        return self._is_tle

    def kill(self) -> None:
        # FIXME(quantum): this is actually a race. The process may exit before we kill it.
        # Under very unlikely circumstances, the pid could be reused and we will end up
        # killing the wrong process.
        if self.returncode is None:
            log.warning('Request the killing of process: %s', self.pid)
            try:
                os.killpg(self.pid, signal.SIGKILL)
            except OSError:
                import traceback

                traceback.print_exc()
        else:
            log.warning('Skipping the killing of process because it already exited: %s', self.pid)

    def _callback(self, syscall) -> bool:
        if self.debugger.abi == PTBOX_ABI_INVALID:
            log.warning('Received invalid ABI when handling syscall %d', syscall)
            return False

        try:
            callback = self._callbacks[self.debugger.abi][syscall]
        except IndexError:
            if self.debugger.abi == PTBOX_ABI_ARM:
                # ARM-specific
                return 0xF0000 < syscall < 0xF0006
            return False

        if callback is not None:
            return callback(self.debugger)
        return False

    def _protection_fault(self, syscall: int, is_update: bool) -> None:
        # When signed, 0xFFFFFFFF is equal to -1, meaning that ptrace failed to read the syscall for some reason.
        # We can't continue debugging as this could potentially be unsafe, so we should exit loudly.
        # See <https://github.com/DMOJ/judge/issues/181> for more details.
        if syscall == -1:
            err = self._last_ptrace_errno
            if err is None:
                log.error('ptrace failed with unknown error')
            else:
                log.error('ptrace error: %d (%s: %s)', err, errno.errorcode[err], os.strerror(err))
            self.protection_fault = (-1, 'ptrace fail', [0] * 6, None)
        else:
            callname = self.debugger.get_syscall_name(syscall)
            self.protection_fault = (
                syscall,
                callname,
                [
                    self.debugger.uarg0,
                    self.debugger.uarg1,
                    self.debugger.uarg2,
                    self.debugger.uarg3,
                    self.debugger.uarg4,
                    self.debugger.uarg5,
                ],
                self._last_ptrace_errno if is_update else None,
            )

    def _ptrace_error(self, error: int) -> None:
        self._last_ptrace_errno = error

    def _cpu_time_exceeded(self) -> None:
        log.warning('SIGXCPU in process %d', self.pid)
        self._is_tle = True

    def _run_process(self) -> Optional[int]:
        try:
            self._spawn(self._executable, self._args, self._env, self._chdir)
        except:  # noqa: E722, need to catch absolutely everything
            self._spawn_error = sys.exc_info()[0]
            self._died.set()
            return None
        finally:
            if self.stdin_needs_close:
                os.close(self._child_stdin)
            if self.stdout_needs_close:
                os.close(self._child_stdout)
            if self.stderr_needs_close:
                os.close(self._child_stderr)

            self._spawned_or_errored.set()

        if not FREEBSD:
            # Adjust OOM score on the child process, sacrificing it before the judge process.
            # This is not possible on FreeBSD.
            try:
                oom_score_adj(OOM_SCORE_ADJ_MAX, self.pid)
            except Exception:
                import traceback

                traceback.print_exc()

        # TODO(tbrindus): this code should be the same as [self.returncode], so it shouldn't be duplicated
        code = self._monitor()

        if self._time and self.execution_time > self._time:
            self._is_tle = True
        self._died.set()

        return code

    def _shocker_thread(self) -> None:
        # On Linux, ignored signals still cause a notification under ptrace.
        # Hence, we use SIGWINCH, harmless and ignored signal to make wait4 return
        # pt_process::monitor, causing time to be updated.
        # On FreeBSD, a signal must not be ignored in order for wait4 to return.
        # Hence, we swallow SIGSTOP, which should never be used anyway, and use it
        # force an update.
        wake_signal = signal.SIGSTOP if FREEBSD else signal.SIGWINCH
        self._spawned_or_errored.wait()

        while not self._died.wait(1):
            if self.execution_time > self._time or self.wall_clock_time > self._wall_time:
                log.warning('Shocker activated and killed %d', self.pid)
                self.kill()
                self._is_tle = True
                break
            try:
                os.killpg(self.pid, wake_signal)
            except OSError:
                pass

    def __init_streams(self, stdin, stdout, stderr) -> None:
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
        elif stderr == STDOUT:
            self._stderr, self._child_stderr = -1, self._child_stdout
        elif isinstance(stderr, int):
            self._stderr, self._child_stderr = -1, stderr
        elif stderr is not None:
            self._stderr, self._child_stderr = -1, stderr.fileno()
        else:
            self._stderr = self._child_stderr = -1

    communicate = _safe_communicate

    def unsafe_communicate(self, input: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        return _safe_communicate(self, input=input, outlimit=sys.maxsize, errlimit=sys.maxsize)


def can_debug(abi: int) -> bool:
    return abi in SUPPORTED_ABIS
