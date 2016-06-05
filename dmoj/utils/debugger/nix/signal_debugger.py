try:
    # Printing stacktrace on SIGUSR1 is implemented natively, because its main use is when
    # the Python interpreter is deadlocked.
    #
    # Python signal handlers defined via the `signal` module do not correspond entirely with native signal handlers:
    # when the Python process receives a signal, it checks if it has any `signal`-defined handlers and if so,
    # runs them. The problem stems from the fact that this may not happen for a while after a native signal is received,
    # or ever (if some native code is hanging while holding the GIL).
    #
    # In that case, a native signal handler is the only hope to get some sort of meaningful data out of the dead
    # Python process.
    from ._nix_debugger import setup_native_traceback
except ImportError as e:
    setup_native_traceback = None


def setup_interactive_debugger():
    import signal
    import code
    import traceback

    # In part from http://stackoverflow.com/questions/132058/showing-the-stack-trace-from-a-running-python-application
    def handle_sigusr2(signum, frame):
        _locals = {'_frame': frame}
        _locals.update(frame.f_globals)
        _locals.update(frame.f_locals)

        message = "Signal received : entering shell.\nTraceback:\n%s" % ''.join(traceback.format_stack(frame))

        console = code.InteractiveConsole(_locals)
        console.interact(message)

    signal.signal(signal.SIGUSR2, handle_sigusr2)


def setup_all_debuggers():
    if setup_native_traceback:
        if not setup_native_traceback():
            pass
    setup_interactive_debugger()
