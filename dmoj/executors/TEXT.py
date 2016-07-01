from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.txt'
    name = 'TEXT'
    command = 'cat'
    command_paths = ['cat']
    test_program = 'echo: Hello, World!\n'
    fs = ['.*\.txt']
    syscalls = ['fadvise64_64', 'fadvise64']

    @classmethod
    def get_command(cls):
        return cls.runtime_dict.get('cat', '/bin/cat')
