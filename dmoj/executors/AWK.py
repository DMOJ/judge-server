from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'awk'
    command = 'awk'
    command_paths = ['mawk', 'gawk', 'awk']
    syscalls = ['getgroups']  # gawk is annoying.
    test_program = '{ print $0 }'

    def get_cmdline(self, **kwargs):
        return [self.get_command(), '-f', self._code]

    @classmethod
    def get_version_flags(cls, command):
        return ['-Wversion', '--version']
