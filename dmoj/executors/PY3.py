from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'python3'
    command_paths = ['python%s' % i for i in ['3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3']]
    test_program = """
import sys
if sys.version_info.major == 3:
    print(sys.stdin.read(), end='')
"""
