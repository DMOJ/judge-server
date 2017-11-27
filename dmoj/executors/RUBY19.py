import os

from .ruby_executor import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY19'
    command_paths = ['ruby1.9', 'ruby1.9.1']

    def get_nproc(self):
        return [-1, 1][os.name == 'nt']
