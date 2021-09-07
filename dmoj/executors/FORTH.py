from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    name = 'FORTH'
    command = 'gforth'
    ext = 'fs'
    test_program = """\
: HELLO  ( -- ) ." echo: Hello, World!" CR ;

HELLO
"""
    fs = [ExactFile('/.gforth-history')]

    def get_cmdline(self, **kwargs):
        return [self.get_command(), self._code, '-e', 'bye']
