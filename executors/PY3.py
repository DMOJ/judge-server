from judgeenv import env
from .python import PythonExecutor

PYTHON_FS = ['/etc/localtime$', '/dev/urandom$', '.*\.(?:so|py[co]?$)', '.*/lib(?:32|64)?/python[\d.]+/.*',
             '.*/lib/locale/', '/usr/lib64', '.*/?pyvenv.cfg$', '/proc/meminfo$']
if 'python3dir' in env['runtime']:
    PYTHON_FS += [str(env['runtime']['python3dir'])]


class Executor(PythonExecutor):
    command = env['runtime'].get('python3')
    test_program = "print(__import__('sys').stdin.read(), end='')"
    name = 'PY3'

    def get_fs(self):
        return PYTHON_FS + [self._dir + '$']

initialize = Executor.initialize
