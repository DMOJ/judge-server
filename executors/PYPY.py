from executors.python import PythonExecutor
from .utils import test_executor
from cptbox import CHROOTSecurity
from judgeenv import env

PYTHON_FS = ['.*\.(?:so|py[co]?$)', '/proc/cpuinfo$', '/proc/meminfo$']


class Executor(PythonExecutor):
    def get_security(self):
        return CHROOTSecurity(PYTHON_FS + ([env['runtime']['pypydir']] if 'pypydir' in env['runtime'] else []))

    def get_executable(self):
        return env['runtime']['pypy']


def initialize():
    if not 'pypy' in env['runtime']:
        return False
    return test_executor('PYPY', Executor, 'print "Hello, World!"')

