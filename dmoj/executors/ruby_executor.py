from .base_executor import ScriptExecutor


class RubyExecutor(ScriptExecutor):
    ext = '.rb'
    name = 'RUBY'
    address_grace = 65536
    test_program = 'puts gets'

    @classmethod
    def get_command(cls):
        return cls.runtime_dict.get(cls.name.lower())

    @classmethod
    def get_find_first_mapping(cls):
        return {cls.name.lower(): cls.command_paths}
