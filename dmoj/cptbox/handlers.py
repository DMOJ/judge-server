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


for err in dir(errno):
    if err[0] == 'E':
        globals()['ACCESS_%s' % err] = errno_handler(getattr(errno, err))
