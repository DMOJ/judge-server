import os
from typing import Dict, List, Optional, Tuple

from dmoj.cptbox.filesystem_policies import ExactDir, ExactFile, FilesystemAccessRule, RecursiveDir
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'rb'
    address_grace = 65536
    test_program = 'puts gets'
    nproc = -1
    command_paths = (
        ['ruby']
        + [f'ruby3.{i}' for i in reversed(range(0, 1))]
        + [f'ruby2.{i}' for i in reversed(range(0, 8))]
        + [f'ruby2{i}' for i in reversed(range(0, 8))]
    )
    syscalls = ['thr_set_name', 'eventfd2', 'specialfd']
    fs = [ExactFile('/proc/self/loginuid')]

    def get_fs(self) -> List[FilesystemAccessRule]:
        fs = super().get_fs()
        home = self.runtime_dict.get(f'{self.get_executor_name().lower()}_home')
        if home is not None:
            fs.append(RecursiveDir(home))
            components = home.split('/')
            components.pop()
            while components and components[-1]:
                fs.append(ExactDir('/'.join(components)))
                components.pop()
        return fs

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        return [command, '--disable-gems', self._code]

    @classmethod
    def get_version_flags(cls, command):
        return ['-v']

    @classmethod
    def get_command(cls) -> Optional[str]:
        name = cls.get_executor_name().lower()
        if name in cls.runtime_dict:
            return cls.runtime_dict[name]
        if f'{name}_home' in cls.runtime_dict:
            return os.path.join(cls.runtime_dict[f'{name}_home'], 'bin', 'ruby')
        return None

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        command = cls.get_command()
        assert command is not None
        return [('ruby', command)]

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        return {cls.name.lower(): cls.command_paths}
