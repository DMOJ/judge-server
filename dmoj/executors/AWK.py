from .base_executor import ScriptExecutor
from dmoj.judgeenv import env


class Executor(ScriptExecutor):
    ext = '.awk'
    name = 'AWK'
    command = 'awk'
    test_program = '{ print $0 }'
    fs = ['.*\.(?:so|awk)', '/dev/(?:urandom|null)$', '/proc/self/maps$']

    def get_cmdline(self):
        return [self.get_command(), '-f', self._code]
