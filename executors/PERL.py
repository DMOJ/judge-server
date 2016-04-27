from .base_executor import ScriptExecutor
from judgeenv import env


class Executor(ScriptExecutor):
    ext = '.pl'
    name = 'PERL'
    command = env['runtime'].get('perl')
    test_program = 'print<>'
    fs = ['.*\.(?:so|p[lm]$)', '/dev/urandom$']

    def get_cmdline(self):
        return ['perl', '-Mre=eval', self._code]

initialize = Executor.initialize
