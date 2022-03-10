from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    command = 'gforth'
    ext = 'fs'
    test_program = """\
: HELLO  ( -- ) ." echo: Hello, World!" CR ;

HELLO
"""

    def get_cmdline(self, **kwargs):
        return [self.get_command(), self._code, '-e', 'bye']
