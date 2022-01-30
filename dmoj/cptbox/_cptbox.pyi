from typing import Callable, Dict, List, Tuple, Optional

PTBOX_ABI_X86: int
PTBOX_ABI_X64: int
PTBOX_ABI_X32: int
PTBOX_ABI_ARM: int
PTBOX_ABI_ARM64: int
PTBOX_ABI_FREEBSD_X64: int
PTBOX_ABI_INVALID: int
PTBOX_ABI_COUNT: int

ALL_ABIS: List[int]
SUPPORTED_ABIS: List[int]

class Debugger:
    syscall: int
    result: int
    errno: int
    arg0: int
    arg1: int
    arg2: int
    arg3: int
    arg4: int
    arg5: int

    uresult: int
    uarg0: int
    uarg1: int
    uarg2: int
    uarg3: int
    uarg4: int
    uarg5: int

    pid: int
    tid: int
    abi: int
    def __init__(self, process: Process): ...
    def readstr(self, address: int, max_size: int = ...) -> str: ...
    def readbytes(self, address: int, size: int) -> bytes: ...
    def on_return(self, callback: Callable[[], None]): ...

class Process:
    debugger: Debugger
    _child_stdin: int
    _child_stdout: int
    _child_stderr: int
    _child_memory: int
    _child_address: int
    _child_personality: int
    _cpu_time: int
    _nproc: int
    _fsize: int
    _cpu_affinity_mask: int

    use_seccomp: bool
    _trace_syscalls: bool
    def create_debugger(self) -> Debugger: ...
    def _callback(self, syscall: int) -> bool: ...
    def _ptrace_error(self, errno: int) -> None: ...
    def _protection_fault(self, syscall: int, is_update: bool) -> None: ...
    def _cpu_time_exceeded(self) -> None: ...
    def _handler(self, abi: int, syscall: int, handler: int) -> None: ...
    def _get_seccomp_whitelist(self) -> List[bool]: ...
    def _get_seccomp_errnolist(self) -> List[int]: ...
    def _spawn(self, file: bytes, args: List[bytes], env: List[bytes], chdir: bytes = ...) -> None: ...
    def _monitor(self) -> int: ...
    @property
    def _exited(self): ...
    @property
    def _exitcode(self): ...
    @property
    def was_initialized(self) -> bool: ...
    @property
    def pid(self) -> int: ...
    @property
    def execution_time(self) -> float: ...
    @property
    def wall_clock_time(self) -> float: ...
    @property
    def cpu_time(self) -> float: ...
    @property
    def max_memory(self) -> int: ...
    @property
    def context_switches(self) -> Tuple[int, int]: ...
    @property
    def signal(self) -> Optional[int]: ...
    @property
    def returncode(self) -> Optional[int]: ...

MAX_SYSCALL_NUMBER: int
NATIVE_ABI: int

PTBOX_SPAWN_FAIL_NO_NEW_PRIVS: int
PTBOX_SPAWN_FAIL_SECCOMP: int
PTBOX_SPAWN_FAIL_TRACEME: int
PTBOX_SPAWN_FAIL_EXECVE: int
PTBOX_SPAWN_FAIL_SETAFFINITY: int

AT_FDCWD: int
bsd_get_proc_cwd: Callable[[int], str]
bsd_get_proc_fdno: Callable[[int, int], str]

memfd_create: Callable[[], int]
memfd_seal: Callable[[int], None]

class BufferProxy:
    def _get_real_buffer(self): ...
