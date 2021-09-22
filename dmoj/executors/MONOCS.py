from typing import List, Tuple

from dmoj.executors.mono_executor import MonoExecutor


class Executor(MonoExecutor):
    ext = 'cs'
    command = 'mono-csc'
    command_paths = ['mono-csc', 'mcs', 'dmcs', 'gmcs']

    test_program = """\
using System;

class test {
    static void Main() {
        string line;
        while (!string.IsNullOrEmpty(line = Console.ReadLine()))
            Console.WriteLine(line);
    }
}"""

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, self._code, '-r:System.Numerics.dll', f'-out:{self.get_compiled_file()}']

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        return [('csc', cls.runtime_dict['mono-csc']), ('mono', cls.runtime_dict['mono'])]
