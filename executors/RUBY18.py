from .ruby_executor import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY18'


initialize = Executor.initialize
