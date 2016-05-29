import os

from dmoj.executors.base_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
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

    def __init__(self, *args, **kwargs):
        self.devnull = open(os.devnull, 'w')
        super(Executor, self).__init__(*args, **kwargs)

    def cleanup(self):
        if hasattr(self, 'devnull'):
            self.devnull.close()
        super(Executor, self).cleanup()

    def get_compile_popen_kwargs(self):
        return {'stdout': self.devnull}

    def get_compile_args(self):
        return [env['runtime']['fpc'], '-Fe/dev/stderr', '-So', '-O2', self._code]

    def get_compile_output(self, process):
        output = process.communicate()[1]
        return output if 'Fatal:' in output or 'Warning:' in output or 'Note:' in output else ''


initialize = Executor.initialize
