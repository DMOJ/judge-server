from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.lua'
    name = 'LUA'
    command = 'lua'
    address_grace = 131072
    test_program = "io.write(io.read('*all'))"
