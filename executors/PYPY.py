from .python_executor import PythonExecutor
from judgeenv import env


class Executor(PythonExecutor):
    command = env['runtime'].get('pypy')
    test_program = "print __import__('sys').stdin.read()"
    name = 'PYPY'
    fs = ['.*\.(?:so|py[co]?$)', '/proc/cpuinfo$', '/proc/meminfo$', '/etc/localtime$', '/dev/urandom$'] + [command] \
      + ([env['runtime']['pypydir']] if 'pypydir' in env['runtime'] else [])

initialize = Executor.initialize
