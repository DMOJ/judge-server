from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'python'
    command_paths = ['python2.7', 'python2', 'python']
    test_program = "print __import__('sys').stdin.read()"
