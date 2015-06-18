from .base_executor import ScriptExecutor
from judgeenv import env


class RubyExecutor(ScriptExecutor):
    ext = '.rb'
    name = 'RUBY'
    address_grace = 65536
    fs = ['.*\.(?:so|rb$)', '/etc/localtime$', '/dev/urandom$', '/proc/self', '/usr/lib/ruby/gems/']
    test_program = 'puts gets'

    @classmethod
    def get_command(cls):
        return env['runtime'].get(cls.name.lower())
