import errno
from asyncio import Protocol
from typing import Callable

from dmoj.cptbox._cptbox import Debugger

DISALLOW = 0
ALLOW = 1
_CALLBACK = 2
STDOUTERR = 3

HandlerCallback = Callable[[Debugger], bool]


class ErrnoHandlerCallback(Protocol):
    errno: int
    error_name: str

    def __call__(self, debugger: Debugger) -> bool:
        pass


def errno_handler(name, code):
    def handler(debugger) -> bool:
        def on_return():
            debugger.errno = code

        debugger.syscall = -1
        debugger.on_return(on_return)
        return True

    handler.error_name = name
    handler.errno = code
    return handler


for err in dir(errno):
    if err[0] == 'E':
        globals()['ACCESS_%s' % err] = errno_handler(err, getattr(errno, err))
