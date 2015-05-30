from .base_executor import CompiledExecutor
from judgeenv import env


class Executor(CompiledExecutor):
    ext = '.d'
    name = 'D'
    address_grace = 32768
    fs = ['.*\.so', '/proc/self/maps$']
    syscalls = ['sched_getaffinity', 'sched_getparam', 'sched_getscheduler',
                'sched_get_priority_min', 'sched_get_priority_max', 'clock_getres']
    command = env['runtime'].get('dmd')
    test_program = '''\
import std.stdio;

void main() {
    writeln(readln());
}
'''

    def get_compile_args(self):
        return [self.get_command(), '-O', '-inline', '-release', '-w', self._code, '-of%s' % self.problem]

initialize = Executor.initialize
