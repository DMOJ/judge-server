from executors.python import PythonExecutor
from .utils import test_executor
from judgeenv import env

try:
    from cptbox import CHROOTSecurity
except ImportError:
    CHROOTSecurity = None

PYTHON_FS = ['.*\.(?:so|py[co]?$)', '/proc/cpuinfo$', '/proc/meminfo$', '/etc/localtime$', '/dev/urandom$']


class Executor(PythonExecutor):
    if CHROOTSecurity is not None:
        def get_security(self):
            return CHROOTSecurity(PYTHON_FS + ([env['runtime']['pypydir']] if 'pypydir' in env['runtime'] else []))

    def get_executable(self):
        return env['runtime']['pypy']

    get_argv0 = get_executable


def initialize():
    if not 'pypy' in env['runtime']:
        return False
    return test_executor('PYPY', Executor, 'print "Hello, World!"')

