from dmoj.executors.mono_executor import MonoExecutor


class Executor(MonoExecutor):
    ext = 'fs'
    command = 'fsharpc'
    compiler_time_limit = 20

    test_program = """\
open System

[<EntryPoint>]
let main argv =
    Console.WriteLine(Console.ReadLine())
    0
"""

    def get_compile_args(self):
        return [
            self.get_command(),
            '--nologo',
            '--optimize',
            '--tailcalls',
            '--out:%s' % self.get_compiled_file(),
            self._code,
        ]

    @classmethod
    def get_version_flags(cls, command):
        return ['--help'] if command == cls.command else super().get_version_flags(command)

    @classmethod
    def get_versionable_commands(cls):
        return ('fsharpc', cls.runtime_dict['fsharpc']), ('mono', cls.runtime_dict['mono'])
