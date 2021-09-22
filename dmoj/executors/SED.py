from typing import List

from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'sed'
    name = 'SED'
    command = 'sed'
    test_program = 's/^//'

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        return [command, '-f', self._code]

    @classmethod
    def get_version_flags(cls, command: str) -> List[str]:
        return ['--version']
