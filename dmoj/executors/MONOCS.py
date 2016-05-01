from dmoj.executors.mono_executor import MonoExecutor
from dmoj.judgeenv import env


class Executor(MonoExecutor):
    ext = '.cs'
    name = 'MONOCS'
    command = env['runtime'].get('mono-csc')

    test_program = '''\
using System;

class test {
    static void Main() {
        string line;
        while (!string.IsNullOrEmpty(line = Console.ReadLine()))
            Console.WriteLine(line);
    }
}'''

    def get_compile_args(self):
        return [self.get_command(), self._code, '-out:%s' % self.get_compiled_file()]

initialize = Executor.initialize
