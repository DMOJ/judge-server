import os

from .PYPY import PYTHON_FS
from executors.python import PythonExecutor
from executors.utils import test_executor
from judgeenv import env

try:
    from cptbox import CHROOTSecurity
    from cptbox.syscalls import *
except ImportError:
    CHROOTSecurity = None


class Executor(PythonExecutor):
    if CHROOTSecurity is not None:
        def get_security(self):
            sec = CHROOTSecurity(PYTHON_FS + ([env['runtime']['pypy3dir']] if 'pypy3dir' in env['runtime'] else []))

            def unsafe_pypy3dir(debugger):
                # Relies on the fact this user can't access here.
                return debugger.readstr(debugger.uarg0).startswith(env['runtime']['pypy3dir'])
            if not os.access(env['runtime']['pypy3dir'], os.W_OK):
                sec[sys_mkdir] = unsafe_pypy3dir
                sec[sys_unlink] = unsafe_pypy3dir
            return sec

    def get_executable(self):
        return env['runtime']['pypy3']


def initialize():
    if not 'pypy3' in env['runtime']:
        return False
    return test_executor('PYPY3', Executor, 'print("Hello, World!")')

