from .python import PythonExecutor
from judgeenv import env

PYTHON_FS = ['.*\.(?:so|py[co]?$)', '/proc/cpuinfo$', '/proc/meminfo$', '/etc/localtime$', '/dev/urandom$']


class Executor(PythonExecutor):
    command = env['runtime'].get('pypy')
    test_program = "print __import__('sys').stdin.read()"
    name = 'PYPY'
    fs = PYTHON_FS + ([env['runtime']['pypydir']] if 'pypydir' in env['runtime'] else [])

initialize = Executor.initialize
