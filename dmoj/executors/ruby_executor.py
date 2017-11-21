import os

from .base_executor import ScriptExecutor


class RubyExecutor(ScriptExecutor):
    ext = '.rb'
    name = 'RUBY'
    address_grace = 65536
    test_program = 'puts gets'

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
