import os
import re

from dmoj.executors.base_executor import BaseExecutor
from dmoj.utils.unicode import utf8bytes


class ScriptExecutor(BaseExecutor):
    def __init__(self, problem_id, source_code, **kwargs):
        super(ScriptExecutor, self).__init__(problem_id, source_code, **kwargs)
        self._code = self._file(
            self.source_filename_format.format(problem_id=problem_id, ext=self.ext))
        self.create_files(problem_id, source_code)

    @classmethod
    def get_command(cls):
        if cls.command in cls.runtime_dict:
            return cls.runtime_dict[cls.command]
        name = cls.get_executor_name().lower()
        if '%s_home' % name in cls.runtime_dict:
            return os.path.join(cls.runtime_dict['%s_home' % name], 'bin', cls.command)

    def get_fs(self):
        home = self.runtime_dict.get('%s_home' % self.get_executor_name().lower())
        fs = super(ScriptExecutor, self).get_fs() + [self._code]
        if home is not None:
            fs.append(re.escape(home))
        return fs

    def create_files(self, problem_id, source_code):
        with open(self._code, 'wb') as fo:
            fo.write(utf8bytes(source_code))

    def get_cmdline(self):
        return [self.get_command(), self._code]

    def get_executable(self):
        return self.get_command()

    def get_env(self):
        env = super(BaseExecutor, self).get_env()
        env_key = self.get_executor_name().lower() + '_env'
        if env_key in self.runtime_dict:
            env = env or {}
            env.update(self.runtime_dict[env_key])
        return env
