from .base_executor import CompiledExecutor
from judgeenv import env


class Executor(CompiledExecutor):
    ext = '.swift'
    name = 'SWIFT'
    fs = ['.*\.so', '/dev/tty$']
    command = env['runtime'].get('swiftc')
    syscalls = ['clock_getres']
    test_program = 'print(readLine()!)'

    def get_compile_args(self):
        return [self.get_command(), self._code]


initialize = Executor.initialize
