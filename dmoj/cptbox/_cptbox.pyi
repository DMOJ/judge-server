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

Debugger: Any
Process: Any

AT_FDCWD: int
bsd_get_proc_cwd: Callable[[int], str]
bsd_get_proc_fdno: Callable[[int, int], str]
