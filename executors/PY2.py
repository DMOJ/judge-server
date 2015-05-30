from judgeenv import env
from .python import PythonExecutor


PYTHON_FS = ['.*\.(?:so|py[co]?$)', '.*/lib(?:32|64)?/python[\d.]+/.*', '.*/lib/locale/', '/proc/meminfo$',
             '/etc/localtime$', '/dev/urandom$']
if 'python2dir' in env:
    PYTHON_FS += [str(env['python3dir'])]


class Executor(PythonExecutor):
    command = env['runtime'].get('python')
    test_program = "print __import__('sys').stdin.read()"
    name = 'PY2'

    def get_fs(self):
        return PYTHON_FS


initialize = Executor.initialize


def aliases():
    if not 'python' in env['runtime']:
        return []
    stderr = Popen(['python', '-V'], executable=env['runtime']['python'], stderr=sPIPE).communicate()[1]
    if '2.7' in stderr:
        return ['PY2', 'PY27']
    else:
        return ['PY2']