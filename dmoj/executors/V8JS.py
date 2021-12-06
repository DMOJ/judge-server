from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'js'
    command = 'v8dmoj'
    test_program = 'print(gets());'
    address_grace = 786432
    nproc = -1

    @classmethod
    def get_version_flags(cls, command):
        return [('-e', 'print(version())')]

    def get_cmdline(self, **kwargs):
        return [self.get_command(), '--stack-size=131072', self._code]  # 128MB Stack Limit
