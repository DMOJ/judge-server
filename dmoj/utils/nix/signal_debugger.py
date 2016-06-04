try:
    from ._debugger import setup_native_traceback
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

    signal.signal(signal.SIGUSR1, handle_sigusr2)


def setup_all_debuggers():
    if setup_native_traceback:
        setup_native_traceback()
    setup_interactive_debugger()
