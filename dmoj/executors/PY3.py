from dmoj.judgeenv import env
from .python_executor import PythonExecutor

PYTHON_FS = ['.*\.(?:py[co]?$)', '.*/lib(?:32|64)?/python[\d.]+/.*',
             '.*/lib/locale/', '/usr/lib64', '.*/?pyvenv.cfg$']
if 'python3dir' in env['runtime']:
    PYTHON_FS += [str(env['runtime']['python3dir'])]


class Executor(PythonExecutor):
    command = 'python3'
    command_paths = ['python%s' for i in ['3.5', '3.4', '3.3', '3.2', '3.1', '3']]
    test_program = "print(__import__('sys').stdin.read(), end='')"
    name = 'PY3'
    fs = PYTHON_FS

    def get_fs(self):
        return super(PythonExecutor, self).get_fs() + [self._dir + '$']
