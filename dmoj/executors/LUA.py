from typing import List

from dmoj.executors.base_executor import VersionFlags
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'lua'
    command = 'lua'
    command_paths = ['lua', 'lua5.3', 'lua5.2', 'lua5.1']
    address_grace = 131072
    test_program = "io.write(io.read('*all'))"

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['-v']
