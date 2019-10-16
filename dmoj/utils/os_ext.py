import ctypes
import ctypes.util
import os
import re
import signal
import subprocess
import sys

from dmoj.utils.unicode import utf8bytes, utf8text


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


def file_info(path, split=re.compile(r'[\s,]').split):
    try:
        return split(utf8text(subprocess.check_output(['file', '-b', '-L', path])))
    except (OSError, subprocess.CalledProcessError):
        raise IOError('call to file(1) failed -- does the utility exist?')


ARCH_X86 = 'x86'
ARCH_X64 = 'x64'
ARCH_X32 = 'x32'
ARCH_ARM = 'arm'
ARCH_A64 = 'arm64'


def file_arch(path):
    info = file_info(path)

    if '32-bit' in info:
        if 'ARM' in info:
            return ARCH_ARM
        return ARCH_X32 if 'x86-64' in info else ARCH_X86
    elif '64-bit' in info:
        if 'aarch64' in info:
            return ARCH_A64
        return ARCH_X64
    return None


INTERPRETER_ARCH = file_arch(sys.executable)


def bool_env(name):
    value = os.environ.get(name, '')
    return value.lower() in ('true', 'yes', '1', 'y', 't')
