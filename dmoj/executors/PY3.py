import os

from dmoj.executors.python_executor import PythonExecutor


class Executor(PythonExecutor):
    command = 'python3'
    command_paths = ['python%s' % i for i in ['3.6', '3.5', '3.4', '3.3', '3.2', '3.1', '3']]
    test_program = "print(__import__('sys').stdin.read(), end='')"
    name = 'PY3'

    def get_env(self):
        env = super(Executor, self).get_env()
        env['PYTHONHOME'] = os.path.dirname(self.get_executable())
        env['PYTHONPATH'] = None
        return env
