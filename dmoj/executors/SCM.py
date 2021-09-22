from typing import List, Tuple

from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.base_executor import VersionFlags
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'scm'
    command = 'chicken-csc'
    command_paths = ['chicken-csc', 'csc']
    compiler_read_fs = [
        RecursiveDir('/var/lib/chicken'),
    ]
    test_program = '(import chicken.io) (map print (read-lines))'

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, self._code]

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        command = cls.get_command()
        assert command is not None
        return [('csc', command)]

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['-version']
