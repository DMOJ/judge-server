from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.pl'
    name = 'PERL'
    command = 'perl'
    test_program = 'print<>'
    fs = ['.*\.p[lm]$']

    def get_cmdline(self):
        return ['perl', '-Mre=eval', self._code]
