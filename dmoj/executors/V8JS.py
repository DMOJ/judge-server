from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.js'
    name = 'V8JS'
    command = 'v8dmoj'
    test_program = 'print(gets());'
    address_grace = 786432
    fs = ['.*\.js']  # v8dmoj binaries are distributed statically linked
