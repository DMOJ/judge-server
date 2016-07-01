from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.txt'
    name = 'TEXT'
    command = 'cat', '/bin/cat'
    test_program = 'echo: Hello, World!\n'
    fs = ['.*\.txt']
    syscalls = ['fadvise64_64', 'fadvise64']
