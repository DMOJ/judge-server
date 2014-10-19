from .ruby import make_executor

_Executor, initialize = make_executor('RUBY19', 'ruby19')


class Executor(_Executor):
    def _nproc(self):
        return 1