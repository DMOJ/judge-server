from .base_executor import ScriptExecutor


 class Executor(ScriptExecutor):
    ext = '.js'
    name = 'MOZJS'
    command = 'js'
    test_program = 'print(readline());'
    nproc = -1
    @classmethod
    def get_version_flags(cls, command):
        return ['-v']
