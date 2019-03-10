from .base_executor import ScriptExecutor

class Executor(ScriptExecutor):
    ext = '.js'
    name = 'MOZJS'
    command_paths = ['js', 'js52']
    test_program = 'print(readline());'
    nproc = -1

    @classmethod
    def get_version_flags(cls, command):
        return ['--version']
