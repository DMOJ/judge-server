from typing import Dict, List, Optional, Tuple

from dmoj.cptbox.filesystem_policies import ExactDir, ExactFile, RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'rkt'
    fs = [RecursiveDir('/etc/racket'), ExactFile('/etc/passwd'), ExactDir('/')]
    compiler_read_fs = [RecursiveDir('~/.local/share/racket')]
    compiler_time_limit = 20

    command = 'racket'

    # Racket SIGABRTs under low-memory conditions before actually crossing the memory limit,
    # so give it a bit of headroom to be properly marked as MLE.
    data_grace = 4096
    address_grace = 131072

    test_program = """\
#lang racket
(displayln (read-line))
"""

    def get_compile_args(self) -> List[str]:
        assert self._code is not None
        return [self.runtime_dict['raco'], 'make', self._code]

    def get_cmdline(self, **kwargs):
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, self._code]

    def get_executable(self) -> str:
        command = self.get_command()
        assert command is not None
        return command

    @classmethod
    def initialize(cls) -> bool:
        if 'raco' not in cls.runtime_dict:
            return False
        return super().initialize()

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        command = cls.get_command()
        assert command is not None
        return [('racket', command)]

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        return {'racket': ['racket'], 'raco': ['raco']}
