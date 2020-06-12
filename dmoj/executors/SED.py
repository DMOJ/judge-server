from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'sed'
    name = 'SED'
    command = 'sed'
    test_program = 's/^//'

    def get_cmdline(self, **kwargs):
        return [self.get_command(), '-f', self._code]

    @classmethod
    def get_version_flags(cls, command):
        return ['--version']
