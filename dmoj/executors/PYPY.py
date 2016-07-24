from dmoj.cptbox.handlers import ACCESS_DENIED
from dmoj.executors.base_executor import reversion
from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'pypy'
    test_program = "print __import__('sys').stdin.read()"
    name = 'PYPY'
    syscalls = [('unlink', ACCESS_DENIED)]

    @classmethod
    def parse_version(cls, command, output):
        match = reversion.match(output)
        if match:
            return match.group(2)  # Prints implemented Python version first
        return None
