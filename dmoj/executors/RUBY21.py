import os

from .ruby_executor import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY21'
    syscalls = ['pipe2', 'sched_getaffinity', ('write', lambda debugger: debugger.arg0 in (1, 2, 4))]

    def get_nproc(self):
        return [-1, 1][os.name == 'nt']
