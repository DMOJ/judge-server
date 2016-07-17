from dmoj.cptbox.handlers import ACCESS_DENIED
from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'pypy'
    test_program = "print __import__('sys').stdin.read()"
    name = 'PYPY'
    syscalls = [('unlink', ACCESS_DENIED)]
