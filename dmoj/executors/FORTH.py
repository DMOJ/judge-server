from dmoj.executors.mixins import ScriptDirectoryMixin
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptDirectoryMixin, ScriptExecutor):
    name = 'FORTH'
    command = 'gforth'
    ext = 'fs'
    test_program = '''\
: HELLO  ( -- ) ." echo: Hello, World!" CR ;

HELLO
'''
    fs = [r'/\.gforth-history$']

    def get_cmdline(self):
        return [self.get_command(), self._code, '-e', 'bye']
