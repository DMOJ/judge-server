import os

from dmoj.cptbox.filesystem_policies import ExactDir, ExactFile, RecursiveDir
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'rb'
    address_grace = 65536
    test_program = 'puts gets'
    nproc = -1
    command_paths = (
        ['ruby']
        + ['ruby3.%d' % i for i in reversed(range(0, 1))]
        + ['ruby2.%d' % i for i in reversed(range(0, 8))]
        + ['ruby2%d' % i for i in reversed(range(0, 8))]
    )
    syscalls = ['thr_set_name', 'eventfd2', 'specialfd']
    fs = [ExactFile('/proc/self/loginuid')]

    def get_fs(self):
        fs = super().get_fs()
        home = self.runtime_dict.get('%s_home' % self.get_executor_name().lower())
        if home is not None:
            fs.append(RecursiveDir(home))
            components = home.split('/')
            components.pop()
            while components and components[-1]:
                fs.append(ExactDir('/'.join(components)))
                components.pop()
        return fs

    def get_cmdline(self, **kwargs):
        return [self.get_command(), '--disable-gems', self._code]

    @classmethod
    def get_version_flags(cls, command):
        return ['-v']

    @classmethod
    def get_command(cls):
        name = cls.get_executor_name().lower()
        if name in cls.runtime_dict:
            return cls.runtime_dict[name]
        if '%s_home' % name in cls.runtime_dict:
            return os.path.join(cls.runtime_dict['%s_home' % name], 'bin', 'ruby')

    @classmethod
    def get_versionable_commands(cls):
        return (('ruby', cls.get_command()),)

    @classmethod
    def get_find_first_mapping(cls):
        return {cls.name.lower(): cls.command_paths}
