import subprocess

from dmoj.executors.mono_executor import MonoExecutor


class Executor(MonoExecutor):
    ext = 'vb'
    command = 'mono-vbnc'
    compile_output_index = 0

    test_program = """\
Imports System

Public Module modmain
   Sub Main()
     Console.WriteLine(Console.ReadLine())
   End Sub
End Module
"""

    def get_compile_args(self):
        return [self.get_command(), '/nologo', '/quiet', '/optimize+', '/out:%s' % self.get_compiled_file(), self._code]

    def get_compile_popen_kwargs(self):
        return {'stdout': subprocess.PIPE, 'stderr': subprocess.STDOUT}

    @classmethod
    def get_versionable_commands(cls):
        return ('vbnc', cls.runtime_dict['mono-vbnc']), ('mono', cls.runtime_dict['mono'])

    @classmethod
    def get_version_flags(cls, command):
        return ['/help'] if command == 'vbnc' else super().get_version_flags(command)

    @classmethod
    def get_find_first_mapping(cls):
        res = super().get_find_first_mapping()
        res['mono-vbnc'] = ['mono-vbnc', 'vbnc']
        return res
