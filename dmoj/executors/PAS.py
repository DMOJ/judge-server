from dmoj.executors.base_executor import CompiledExecutor
from dmoj.executors.mixins import NullStdoutMixin
from dmoj.judgeenv import env


class Executor(NullStdoutMixin, CompiledExecutor):
    ext = '.pas'
    name = 'PAS'
    fs = ['.*\.so']
    command = env['runtime'].get('fpc')
    test_program = '''\
var line : string;
begin
    readln(line);
    writeln(line);
end.
'''

    def get_compile_args(self):
        return [env['runtime']['fpc'], '-Fe/dev/stderr', '-So', '-O2', self._code]

    def get_compile_output(self, process):
        output = process.communicate()[1]
        return output if 'Fatal:' in output or 'Warning:' in output or 'Note:' in output else ''
