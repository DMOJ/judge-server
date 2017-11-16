from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.js'
    name = 'V8JS'
    command = 'v8dmoj'
    test_program = 'print(gets());'
    address_grace = 786432
    nproc = -1

    @classmethod
    def get_version_flags(cls, command):
        return [('-e', 'print(version())')]
