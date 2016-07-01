from dmoj.judgeenv import env
from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    name = 'FORTH'
    command = 'gforth'
    ext = '.fs'
    test_program = '''\
: HELLO  ( -- ) ." echo: Hello, World!" CR ;

HELLO
'''
    fs = ['.*?\.(?:so|fs|fi|gforth-history)']

    def get_cmdline(self):
        return [self.get_command(), self._code, '-e', 'bye']
