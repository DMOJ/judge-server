from .utils import test_executor
from cptbox import CHROOTSecurity
from judgeenv import env
from subprocess import Popen, PIPE as sPIPE
from .python import PythonExecutor

PYTHON_FS = ['.*\.(?:so|py[co]?$)', '.*/lib(?:32|64)?/python[\d.]+/.*', '.*/lib/locale/', '/proc/meminfo$',
             '/etc/localtime$', '/dev/urandom$']
if 'python2dir' in env:
    PYTHON_FS += [str(env['python3dir'])]


class Executor(PythonExecutor):
    def get_security(self):
        return CHROOTSecurity(PYTHON_FS)

    def get_executable(self):
        return env['runtime']['python']


def initialize():
    if not 'python' in env['runtime']:
        return False
    return test_executor('PY2', Executor, 'print "Hello, World!"')


def aliases():
    if not 'python' in env['runtime']:
        return []
    stderr = Popen(['python', '-V'], executable=env['runtime']['python'], stderr=sPIPE).communicate()[1]
    if '2.7' in stderr:
        return ['PY2', 'PY27']
    else:
        return ['PY2']