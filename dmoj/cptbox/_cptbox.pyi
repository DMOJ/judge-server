from typing import Any, Callable

DEBUGGER_X86: int
DEBUGGER_X64: int
DEBUGGER_X86_ON_X64: int
DEBUGGER_X32: int
DEBUGGER_ARM: int
DEBUGGER_ARM64: int

Debugger: Any
Process: Any

AT_FDCWD: int
bsd_get_proc_cwd: Callable[[int], str]
bsd_get_proc_fdno: Callable[[int, int], str]
