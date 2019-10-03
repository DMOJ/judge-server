import ctypes
import ctypes.util
import signal


# in large part from http://code.activestate.com/recipes/578899-strsignal/
def strsignal(signo):
    libc = ctypes.CDLL(ctypes.util.find_library("c"))
    strsignal_c = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_int)(("strsignal", libc), ((1,),))
    NSIG = signal.NSIG

    # The behavior of the C library strsignal() is unspecified if
    # called with an out-of-range argument.  Range-check on entry
    # _and_ NULL-check on exit.
    if 0 <= signo < NSIG:
        s = strsignal_c(signo)
        if s:
            return s.decode("utf-8")
    return "Unknown signal %d" % signo
