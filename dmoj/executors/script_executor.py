import os
from typing import Dict, List, Optional

from dmoj.cptbox.filesystem_policies import ExactFile, FilesystemAccessRule, RecursiveDir
from dmoj.executors.base_executor import BaseExecutor
from dmoj.utils.unicode import utf8bytes


class ScriptExecutor(BaseExecutor):
    def __init__(self, problem_id: str, source_code: bytes, **kwargs) -> None:
        super().__init__(problem_id, source_code, **kwargs)
        self._code = self._file(self.source_filename_format.format(problem_id=problem_id, ext=self.ext))
        self.create_files(problem_id, source_code)

    @classmethod
    def get_command(cls) -> Optional[str]:
        if cls.command in cls.runtime_dict:
            return cls.runtime_dict[cls.command]
        name = cls.get_executor_name().lower()
        if '%s_home' % name in cls.runtime_dict:
            assert cls.command is not None
            return os.path.join(cls.runtime_dict['%s_home' % name], 'bin', cls.command)
        return None

    def get_fs(self) -> List[FilesystemAccessRule]:
        home = self.runtime_dict.get('%s_home' % self.get_executor_name().lower())
        fs = super().get_fs() + [ExactFile(self._code)]
        if home is not None:
            fs += [RecursiveDir(home)]
        return fs

    def create_files(self, problem_id: str, source_code: bytes) -> None:
        with open(self._code, 'wb') as fo:
            fo.write(utf8bytes(source_code))

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        return [command, self._code]

    def get_executable(self) -> str:
        command = self.get_command()
        assert command is not None
        return command

    def get_env(self) -> Dict[str, str]:
        env = super().get_env()
        env_key = self.get_executor_name().lower() + '_env'
        if env_key in self.runtime_dict:
            env = env or {}
            env.update(self.runtime_dict[env_key])
        return env
