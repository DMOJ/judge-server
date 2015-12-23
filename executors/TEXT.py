from .base_executor import ScriptExecutor
from judgeenv import env


class Executor(ScriptExecutor):
    ext = '.txt'
    name = 'TEXT'
    command = env['runtime'].get('cat', '/bin/cat')
    test_program = 'echo: Hello, World!\n'
    fs = ['.*\.(?:so|txt)']
    syscalls = ['fadvise64_64', 'fadvise64']

initialize = Executor.initialize
