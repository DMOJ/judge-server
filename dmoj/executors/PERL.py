from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'pl'
    command = 'perl'
    fs = [RecursiveDir('/etc/perl')]
    test_program = 'print<>'
    syscalls = ['umtx_op']

    def get_cmdline(self, **kwargs):
        return ['perl', '-Mre=eval', self._code]
