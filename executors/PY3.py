from cptbox import CHROOTSecurity
from .utils import test_executor
from judgeenv import env
from .python import PythonExecutor

PYTHON_FS = ['/etc/localtime$', '/dev/urandom$', '.*\.(?:so|py[co]?$)', '.*/lib(?:32|64)?/python[\d.]+/.*',
             '.*/lib/locale/', '/usr/lib64', '.*/?pyvenv.cfg$', '/proc/meminfo$']
if 'python3dir' in env:
    PYTHON_FS += [str(env['python3dir'])]


class Executor(PythonExecutor):
    def get_security(self):
        return CHROOTSecurity(PYTHON_FS + [self._dir + '$'])

    def get_executable(self):
        return env['runtime']['python3']


def initialize():
    if not 'python3' in env['runtime']:
        return False
    return test_executor('PY3', Executor, 'print("Hello, World!")')
