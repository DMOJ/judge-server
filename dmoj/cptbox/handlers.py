import errno

DISALLOW = 0
ALLOW = 1
_CALLBACK = 2
STDOUTERR = 3


def errno_handler(code):
    def handler(debugger):
        def on_return():
            debugger.result = -code

        debugger.syscall = -1
        debugger.on_return(on_return)
        return True
    return handler

ACCESS_DENIED = errno_handler(errno.EACCES)
ACCESS_EPERM = errno_handler(errno.EPERM)
ACCESS_ENOENT = errno_handler(errno.ENOENT)
