from .ruby import make_executor
from cptbox.syscalls import *

_Executor, initialize = make_executor('RUBY19', 'ruby19')


class Executor(_Executor):
    def _security(self):
        security = super(Executor, self)._security()
        clone_count = [0]

        def clone_handler(debugger):
            clone_count[0] += 1
            return clone_count[0] <= 1

        security[sys_clone] = clone_handler
        return security