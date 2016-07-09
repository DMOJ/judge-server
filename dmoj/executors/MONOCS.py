from dmoj.executors.mono_executor import MonoExecutor


class Executor(MonoExecutor):
    ext = '.cs'
    name = 'MONOCS'
    command = 'mono-csc'
    command_paths = ['mono-csc', 'dmcs', 'mcs', 'gmcs']

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
        return [self.get_command(), self._code, '-r:System.Numerics.dll', '-out:%s' % self.get_compiled_file()]
