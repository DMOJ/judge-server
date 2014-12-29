from .ruby import make_executor, make_initialize

try:
    from cptbox.syscalls import *
    from cptbox import ALLOW
except ImportError:
    cptbox = False
else:
    cptbox = True


class Executor(make_executor('ruby21')):
    def _nproc(self):
        return -1

    if cptbox:
        def _security(self):
            sec = super(Executor, self)._security()
            sec[sys_sched_getaffinity] = ALLOW
            sec[sys_pipe2] = ALLOW
            sec[sys_write] = lambda debugger: debugger.arg0 in (1, 2, 4)
            return sec

initialize = make_initialize('RUBY21', 'ruby21', Executor)
