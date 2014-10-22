from cptbox.syscalls import *
from cptbox import ALLOW
from .ruby import make_executor, make_initialize


class Executor(make_executor('ruby21')):
    def _nproc(self):
        return -1

    def _security(self):
        sec = super(Executor, self)._security()
        sec[sys_sched_getaffinity] = ALLOW
        return sec

initialize = make_initialize('RUBY21', 'ruby21', Executor)
