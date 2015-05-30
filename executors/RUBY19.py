import os
from .ruby import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY19'

    def get_nproc(self):
        return [-1, 1][os.name == 'nt']

    def get_security(self):
        from cptbox.syscalls import sys_write
        sec = super(Executor, self).get_security()
        sec[sys_write] = lambda debugger: debugger.arg0 in (1, 2, 4)
        return sec

initialize = Executor.initialize
