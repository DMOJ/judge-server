from dmoj.judgeenv import env
from .python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = env['runtime'].get('python')
    test_program = "print __import__('sys').stdin.read()"
    name = 'PY2'
    fs = ['.*\.(?:so|py[co]?$)', '.*/lib(?:32|64)?/python[\d.]+/.*', '.*/lib/locale/', '/proc/meminfo$',
          '/etc/localtime$', '/dev/urandom$']
    if 'python2dir' in env:
        fs += [str(env['python3dir'])]
