from dmoj.cptbox.handlers import ACCESS_DENIED
from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'pypy3'
    test_program = "print(__import__('sys').stdin.read(), end='')"
    name = 'PYPY3'
    syscalls = [('unlink', ACCESS_DENIED), ('mkdir', ACCESS_DENIED)]
