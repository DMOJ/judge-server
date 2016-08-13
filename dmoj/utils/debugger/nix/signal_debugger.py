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
    from ._nix_debugger import setup_native_traceback as setup_all_debuggers
except ImportError as e:
    def setup_all_debuggers():
        pass
