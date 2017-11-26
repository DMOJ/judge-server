from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.awk'
    name = 'AWK'
    command = 'awk'
    command_paths = ['mawk', 'gawk', 'awk']
    syscalls = ['getgroups']  # gawk is annoying.
    test_program = '{ print $0 }'

    def get_cmdline(self):
        return [self.get_command(), '-f', self._code]

    @classmethod
    def get_version_flags(cls, command):
        return ['-Wversion', '--version']
