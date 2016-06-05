try:
    from ._win_debugger import setup_native_traceback
except ImportError as e:
    import traceback
    traceback.print_exc()
    setup_native_traceback = None


def setup_all_debuggers():
    if setup_native_traceback is not None:
        setup_native_traceback()
