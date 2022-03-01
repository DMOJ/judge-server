from dmoj.cptbox._cptbox import Debugger

ALLOW: int
DISALLOW: int
_CALLBACK: int

class ErrnoHandlerCallback:
    errno: int
    error_name: str
    def __call__(self, debugger: Debugger) -> bool: ...

ACCESS_EACCES: ErrnoHandlerCallback
ACCESS_EAGAIN: ErrnoHandlerCallback
ACCESS_EFAULT: ErrnoHandlerCallback
ACCESS_EINVAL: ErrnoHandlerCallback
ACCESS_ENOENT: ErrnoHandlerCallback
ACCESS_EPERM: ErrnoHandlerCallback
ACCESS_ENAMETOOLONG: ErrnoHandlerCallback
