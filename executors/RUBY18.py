from .ruby import make_executor, make_initialize

Executor = make_executor('ruby')
initialize = make_initialize('RUBY18', 'ruby', Executor)
