from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'python3'
    command_paths = [f'python3.{i}' for i in reversed(range(1, 10))] + ['python3']
    test_program = "print(__import__('sys').stdin.read(), end='')"
    name = 'PY3'
