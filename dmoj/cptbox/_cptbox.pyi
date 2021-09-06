from typing import Any, Callable, List

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

    def readstr(self, address: int, max_size: int = ...) -> str: ...
    def on_return(self, callback: Callable[[], None]): ...


Process: Any

AT_FDCWD: int
bsd_get_proc_cwd: Callable[[int], str]
bsd_get_proc_fdno: Callable[[int, int], str]

memory_fd_create: Callable[[], int]
memory_fd_seal: Callable[[int], None]
