from .base_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = '.d'
    name = 'D'
    address_grace = 32768
    fs = ['.*\.so', '/proc/self/maps$']
    command = env['runtime'].get('dmd')
    test_program = '''\
import std.stdio;

void main() {
    writeln(readln());
}
'''

    def get_compile_args(self):
        return [self.get_command(), '-O', '-inline', '-release', '-w', self._code, '-of%s' % self.problem]
