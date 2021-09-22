import os
from typing import Dict, List

from dmoj.cptbox.filesystem_policies import ExactFile, FilesystemAccessRule
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = 't'
    command = 'tprolog'
    test_program = """\
var echo : string
get echo : *
put echo
"""

    def get_fs(self) -> List[FilesystemAccessRule]:
        assert self._code is not None
        return super().get_fs() + [ExactFile(self._code + 'bc')]

    def get_compile_args(self) -> List[str]:
        tprologc = self.runtime_dict['tprologc']
        assert self._code is not None
        return [tprologc, self._code, os.path.dirname(tprologc)]

    def get_cmdline(self, **kwargs) -> List[str]:
        assert self._code is not None
        return [self.runtime_dict['tprolog'], self._code + 'bc']

    def get_executable(self) -> str:
        command = self.get_command()
        assert command is not None
        return command

    @classmethod
    def initialize(cls) -> bool:
        if 'tprolog' not in env['runtime'] or 'tprologc' not in env['runtime']:
            return False
        return super().initialize()

    @classmethod
    def get_find_first_mapping(cls) -> Dict[str, List[str]]:
        return {'tprolog': ['tprolog'], 'tprologc': ['tprologc']}
