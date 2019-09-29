from dmoj.executors.mixins import EmulateTerminalMixin
from .base_executor import CompiledExecutor


class Executor(EmulateTerminalMixin, CompiledExecutor):
    ext = 'swift'
    name = 'SWIFT'
    command = 'swiftc'
    test_program = 'print(readLine()!)'

    def get_compile_args(self):
        return [self.get_command(), self._code]
