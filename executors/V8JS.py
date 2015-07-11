from .base_executor import ScriptExecutor
from judgeenv import env


class Executor(ScriptExecutor):
    ext = '.js'
    name = 'V8JS'
    command = env['runtime'].get('v8dmoj')
    test_program = 'print(gets());'
    address_grace = 786432
    fs = []  # v8dmoj binaries are distributed statically linked


initialize = Executor.initialize
