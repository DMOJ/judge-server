
from .base_executor import ScriptExecutor
from judgeenv import env


class Executor(ScriptExecutor):
    ext = '.sed'
    name = 'SED'
    command = env['runtime'].get('sed', '/bin/sed')
    test_program = '''s/.*/echo: Hello, World!/
q'''
    fs = ['.*\.(so|sed)', '/dev/urandom$', '/proc/self/maps$', '/proc/filesystems$', '/+lib/charset.alias$']
    syscalls = ['getgroups32', 'statfs64']

    def get_cmdline(self):
        return [self.get_command(), '-f', self._code]

initialize = Executor.initialize
