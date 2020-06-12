from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'pl'
    name = 'PERL'
    command = 'perl'
    fs = ['/etc/perl/.*?']
    test_program = 'print<>'
    syscalls = ['umtx_op']

    def get_cmdline(self, **kwargs):
        return ['perl', '-Mre=eval', self._code]
