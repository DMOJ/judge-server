from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.awk'
    name = 'AWK'
    command = 'awk'
    command_paths = ['gawk', 'mawk', 'awk']
    test_program = '{ print $0 }'

    def get_cmdline(self):
        return [self.get_command(), '-f', self._code]
