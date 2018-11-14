from .base_executor import CompiledExecutor
from dmoj.executors.mixins import EmulateTerminalMixin


class Executor(EmulateTerminalMixin, CompiledExecutor):
    ext = '.cr'
    name = 'CYT'
    command = 'crystal'
    syscalls = ['epoll_create', 'epoll_wait', 'poll', 'epoll_create1', 'pipe2']
    test_program = 'puts gets'

    def get_compile_args(self):
        return [self.get_command(), 'build', self._code]
