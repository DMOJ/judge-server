from .base_executor import ScriptExecutor


class MetaRubyExecutor(type):
    def __new__(mcs, name, bases, dict):
        if 'name' in dict:
            dict['command'] = dict['name'].lower()
        return super(MetaRubyExecutor, mcs).__new__(mcs, name, bases, dict)


class RubyExecutor(ScriptExecutor):
    __metaclass__ = MetaRubyExecutor

    ext = '.rb'
    name = 'RUBY'
    address_grace = 65536
    test_program = 'puts gets'

    @classmethod
    def get_version_flags(cls, command):
        return ['-v']

    @classmethod
    def get_versionable_commands(cls):
        return ('ruby', cls.runtime_dict[cls.name.lower()]),

    @classmethod
    def get_find_first_mapping(cls):
        return {cls.name.lower(): cls.command_paths}
