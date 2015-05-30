from .base_executor import CompiledExecutor
from judgeenv import env


class Executor(CompiledExecutor):
    ext = '.d'
    name = 'D'
    address_grace = 32768
    fs = ['.*\.so', '/proc/self/maps$']
    command = env['runtime'].get('dmd')

    def get_compile_args(self):
        return [self.get_command(), '-O', '-inline', '-release', '-w', self._code, '-of%s' % self.problem]

    def get_security(self):
        from cptbox import ALLOW
        from cptbox.syscalls import sys_sched_getaffinity, sys_sched_getparam, sys_sched_getscheduler, \
                                    sys_sched_get_priority_min, sys_sched_get_priority_max, sys_clock_getres

        sec = super(Executor, self).get_security()
        sec[sys_sched_getaffinity] = ALLOW
        sec[sys_sched_getparam] = ALLOW
        sec[sys_sched_getscheduler] = ALLOW
        sec[sys_sched_get_priority_min] = ALLOW
        sec[sys_sched_get_priority_max] = ALLOW
        sec[sys_clock_getres] = ALLOW
        return sec

initialize = Executor.initialize
