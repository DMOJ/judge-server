from dmoj.executors.mono_executor import MonoExecutor


class Executor(MonoExecutor):
    ext = '.fs'
    name = 'MONOFS'
    command = 'fsharpc'

    test_program = '''\
open System

[<EntryPoint>]
let main argv =
    Console.WriteLine(Console.ReadLine())
    0
'''

    def get_compile_args(self):
        return [self.get_command(), '--nologo', '--optimize', '--tailcalls', '--out:%s' % self.get_compiled_file(),
                self._code]
