from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.awk'
    name = 'AWK'
    command = 'awk'
    test_program = '{ print $0 }'
    fs = ['.*\.awk']

    def get_cmdline(self):
        return [self.get_command(), '-f', self._code]
