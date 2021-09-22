import os
from typing import Dict, List, Optional, Tuple

from dmoj.cptbox.filesystem_policies import ExactFile, FilesystemAccessRule
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'coffee'
    nproc = -1
    command = 'node'
    syscalls = [
        'capget',
        'eventfd2',
        'newselect',
        'sched_yield',
        'select',
        'setrlimit',
        'statx',
    ]
    test_program = """\
process.stdin.on 'readable', () ->
  chunk = process.stdin.read()
  if chunk != null
    process.stdout.write chunk
"""
    address_grace = 1048576

    @classmethod
    def initialize(cls) -> bool:
        if 'coffee' not in cls.runtime_dict or not os.path.isfile(cls.runtime_dict['coffee']):
            return False
        return super().initialize()

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        return [command, self.runtime_dict['coffee'], self._code]

    def get_fs(self) -> List[FilesystemAccessRule]:
        return super().get_fs() + [ExactFile(self.runtime_dict['coffee']), ExactFile(self._code)]

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        return [('coffee', cls.runtime_dict['coffee']), ('node', cls.runtime_dict['node'])]

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        return {'node': ['nodejs', 'node'], 'coffee': ['coffee']}
