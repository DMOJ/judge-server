import subprocess

from .mono_executor import MonoExecutor
from judgeenv import env


class Executor(MonoExecutor):
    ext = '.vb'
    name = 'MONOVB'
    command = env['runtime'].get('mono-vbnc')

    test_program = '''\
Imports System

Public Module modmain
   Sub Main()
     Console.WriteLine(Console.ReadLine())
   End Sub
End Module
'''

    def get_compile_args(self):
        return [self.get_command(), '/nologo', '/quiet', '/optimize+', '/out:%s' % self.get_compiled_file(), self._code]

    def get_compile_popen_kwargs(self):
        return {'stdout': subprocess.PIPE, 'stderr': subprocess.STDOUT}

    def get_compile_output(self, process):
        return process.communicate()[0]

initialize = Executor.initialize
