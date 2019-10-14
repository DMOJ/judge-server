import os
import re

from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'rb'
    name = 'RUBY2'
    address_grace = 65536
    test_program = 'puts gets'
    nproc = -1
    command_paths = (['ruby2.%d' % i for i in reversed(range(0, 7))] +
                     ['ruby2%d' % i for i in reversed(range(0, 7))])
    syscalls = ['poll', 'thr_set_name']
    fs = ['/proc/self/loginuid$']

    def get_fs(self):
        fs = super().get_fs()
        home = self.runtime_dict.get('%s_home' % self.get_executor_name().lower())
        if home is not None:
            fs.append(re.escape(home))
            components = home.split('/')
            components.pop()
            while components and components[-1]:
                fs.append(re.escape('/'.join(components)) + '$')
                components.pop()
        return fs

    def get_cmdline(self):
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
        return ('ruby', cls.get_command()),

    @classmethod
    def get_find_first_mapping(cls):
        return {cls.name.lower(): cls.command_paths}
