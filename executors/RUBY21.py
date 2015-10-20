import os

from .ruby import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY21'

    def get_nproc(self):
        return [-1, 1][os.name == 'nt']

    def get_security(self):
        from cptbox.syscalls import sys_write, sys_sched_getaffinity, sys_pipe2
        from cptbox import ALLOW

        sec = super(Executor, self).get_security()
        sec[sys_sched_getaffinity] = ALLOW
        sec[sys_pipe2] = ALLOW
        sec[sys_write] = lambda debugger: debugger.arg0 in (1, 2, 4)
        return sec

initialize = Executor.initialize