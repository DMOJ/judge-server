from .base_executor import ScriptExecutor
from dmoj.judgeenv import env


class Executor(ScriptExecutor):
    ext = '.lua'
    name = 'LUA'
    command = 'lua'
    address_grace = 131072
    test_program = "io.write(io.read('*all'))"
    fs = ['.*\.(so|lua$)']
