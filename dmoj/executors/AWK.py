from typing import List

from dmoj.executors.base_executor import VersionFlags
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'awk'
    command = 'awk'
    command_paths = ['mawk', 'gawk', 'awk']
    syscalls = ['getgroups']  # gawk is annoying.
    test_program = '{ print $0 }'

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        return [command, '-f', self._code]

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['-Wversion', '--version']
