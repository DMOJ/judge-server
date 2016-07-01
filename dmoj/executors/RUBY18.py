from .ruby_executor import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY18'
    command_paths = ['ruby1.8']
