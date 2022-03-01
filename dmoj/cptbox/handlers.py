import errno

from dmoj.cptbox._cptbox import Debugger

DISALLOW = 0
ALLOW = 1
_CALLBACK = 2


class ErrnoHandlerCallback:
    errno: int
    error_name: str

    def __init__(self, error_name: str, errno: int) -> None:
        self.errno = errno
        self.error_name = error_name

    def __call__(self, debugger: Debugger) -> bool:
        def on_return():
            debugger.errno = self.errno

        debugger.syscall = -1
        debugger.on_return(on_return)
        return True


for code, name in errno.errorcode.items():
    globals()[f'ACCESS_{name}'] = ErrnoHandlerCallback(name, code)
