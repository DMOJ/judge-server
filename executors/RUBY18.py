from .ruby import make_executor, make_initialize

Executor = make_executor('ruby18')
initialize = make_initialize('RUBY18', 'ruby18', Executor)
