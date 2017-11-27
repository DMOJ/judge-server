import os

from .ruby_executor import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY2'
    command_paths = (['ruby2.%d' % i for i in reversed(range(0, 5))] +
                     ['ruby2%d' % i for i in reversed(range(0, 5))])
    syscalls = ['pipe2', 'poll', 'thr_set_name']
    fs = ['/proc/self/loginuid$']

    def get_nproc(self):
        return [-1, 1][os.name == 'nt']
