import ctypes
import ctypes.util
import signal
from typing import Optional

from dmoj.utils.unicode import utf8bytes

OOM_SCORE_ADJ_MAX = 1000
OOM_SCORE_ADJ_MIN = -1000


def oom_score_adj(score: int, to: Optional[int] = None) -> None:
    if not (OOM_SCORE_ADJ_MIN <= score <= OOM_SCORE_ADJ_MAX):
        raise OSError()

    with open(f'/proc/{"self" if to is None else to}/oom_score_adj', 'wb') as f:
        f.write(utf8bytes(str(score)))


try:
    from signal import strsignal as _strsignal
except ImportError:  # before Python 3.8

    def strsignal(signo: int) -> str:
        # in large part from http://code.activestate.com/recipes/578899-strsignal/
        libc = ctypes.CDLL(ctypes.util.find_library('c'))
        strsignal_c = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_int)(('strsignal', libc), ((1,),))
        NSIG = signal.NSIG

        # The behavior of the C library strsignal() is unspecified if
        # called with an out-of-range argument.  Range-check on entry
        # _and_ NULL-check on exit.
        if 0 <= signo < NSIG:
            s = strsignal_c(signo)
            if s:
                return s.decode('utf-8')
        return f'Unknown signal {signo}'

else:

    def strsignal(signo: int) -> str:
        return _strsignal(signo) or f'Unknown signal {signo}'
