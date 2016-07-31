import os
from dmoj.executors.base_executor import reversion
from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'pypy'
    test_program = "print __import__('sys').stdin.read()"
    name = 'PYPY'
    if os.name != 'nt':
        from dmoj.cptbox.handlers import ACCESS_DENIED
        syscalls = [('unlink', ACCESS_DENIED)]

    @classmethod
    def parse_version(cls, command, output):
        try:
            return reversion.findall(output)[1]  # Prints implemented Python version first
        except:
            return None