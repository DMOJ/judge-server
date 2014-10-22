from .ruby import make_executor, make_initialize


class Executor(make_executor('ruby19')):
    def _nproc(self):
        return -1

initialize = make_initialize('RUBY19', 'ruby19', Executor)
