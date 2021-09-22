from typing import List, Tuple

from dmoj.executors.base_executor import VersionFlags
from dmoj.executors.mono_executor import MonoExecutor


class Executor(MonoExecutor):
    ext = 'fs'
    command = 'fsharpc'
    compiler_time_limit = 20

    test_program = """\
open System

[<EntryPoint>]
let main argv =
    Console.WriteLine(Console.ReadLine())
    0
"""

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [
            command,
            '--nologo',
            '--optimize',
            '--tailcalls',
            f'--out:{self.get_compiled_file()}',
            self._code,
        ]

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['--help'] if command == cls.command else super().get_version_flags(command)

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        return [('fsharpc', cls.runtime_dict['fsharpc']), ('mono', cls.runtime_dict['mono'])]
