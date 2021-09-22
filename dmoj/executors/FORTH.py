from typing import List

from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    command = 'gforth'
    ext = 'fs'
    test_program = """\
: HELLO  ( -- ) ." echo: Hello, World!" CR ;

HELLO
"""

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, self._code, '-e', 'bye']
