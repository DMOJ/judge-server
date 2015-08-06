
from .base_executor import ScriptExecutor
from judgeenv import env


class Executor(ScriptExecutor):
    ext = '.awk'
    name = 'AWK'
    command = env['runtime'].get('awk')
    test_program = 'BEGIN { print "echo: Hello, World!" }'
    fs = ['.*\.(so|awk)', '/dev/urandom$', '/proc/self/maps$']
    syscalls = ['getgroups32']

    def get_cmdline(self):
        return [self.get_command(), '-f', self._code]

initialize = Executor.initialize
