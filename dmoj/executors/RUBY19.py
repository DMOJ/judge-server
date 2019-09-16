import os

from .ruby_executor import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY19'
    nproc = -1
    command_paths = ['ruby1.9', 'ruby1.9.1']

