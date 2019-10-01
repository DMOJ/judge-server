import os
import re

from dmoj.executors.base_executor import BaseExecutor
from dmoj.utils.unicode import utf8bytes


class ScriptExecutor(BaseExecutor):
    def __init__(self, problem_id: str, source_code: str, **kwargs):
        super(ScriptExecutor, self).__init__(problem_id: str, source_code: str, **kwargs)
        self._code = self._file(
            self.source_filename_format.format(problem_id=problem_id, ext=self.ext))
        self.create_files(problem_id, source_code)

    @classmethod
    def get_command(cls) -> str:
        if cls.command in cls.runtime_dict:
            return cls.runtime_dict[cls.command]
        name = cls.get_executor_name().lower()
        if '%s_home' % name in cls.runtime_dict:
            return os.path.join(cls.runtime_dict['%s_home' % name], 'bin', cls.command)

    def get_fs(self) -> list:
        home = self.runtime_dict.get('%s_home' % self.get_executor_name().lower())
        fs = super(ScriptExecutor, self).get_fs() + [self._code]
        if home is not None:
            fs.append(re.escape(home))
        return fs

    def create_files(self, problem_id: str, source_code: str) -> None:
        with open(self._code, 'wb') as fo:
            fo.write(utf8bytes(source_code))

    def get_cmdline(self) -> List[str, str]:
        return [self.get_command(), self._code]

    def get_executable(self) -> str:
        return self.get_command()

    def get_env(self) -> dict:
        env = super(BaseExecutor, self).get_env()
        env_key = self.get_executor_name().lower() + '_env'
        if env_key in self.runtime_dict:
            env = env or {}
            env.update(self.runtime_dict[env_key])
        return env
