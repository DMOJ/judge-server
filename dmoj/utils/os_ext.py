import ctypes
import ctypes.util
import os
import signal

from dmoj.utils.unicode import utf8bytes

OOM_SCORE_ADJ_MAX = 1000
OOM_SCORE_ADJ_MIN = -1000


def oom_score_adj(score, to=None):
    if not (OOM_SCORE_ADJ_MIN <= score <= OOM_SCORE_ADJ_MAX):
        raise OSError()

    if to is None:
        to = 'self'

    with open('/proc/%s/oom_score_adj' % to, 'wb') as f:
        f.write(utf8bytes(str(score)))


def strsignal(signo):
    # in large part from http://code.activestate.com/recipes/578899-strsignal/
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


def find_exe_in_path(path):
    if os.path.isabs(path):
        return path
    if os.sep in path:
        return os.path.abspath(path)
    for dir in os.environ.get('PATH', os.defpath).split(os.pathsep):
        p = os.path.join(dir, path)
        if os.access(p, os.X_OK):
            return utf8bytes(p)
    raise OSError()


def bool_env(name):
    value = os.environ.get(name, '')
    return value.lower() in ('true', 'yes', '1', 'y', 't')
