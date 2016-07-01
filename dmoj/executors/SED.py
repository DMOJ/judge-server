
from .base_executor import ScriptExecutor
from dmoj.judgeenv import env


class Executor(ScriptExecutor):
    ext = '.sed'
    name = 'SED'
    command = 'sed', '/bin/sed'
    test_program = '''s/.*/echo: Hello, World!/
q'''
    fs = ['.*\.so', '/proc/filesystems$', '/+lib/charset.alias$']
    syscalls = ['statfs64', 'statfs']

    def get_cmdline(self):
        return [self.get_command(), '-f', self._code]
