import subprocess
from typing import Any, Dict, List, Optional, Tuple

from dmoj.executors.base_executor import VersionFlags
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

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, '/nologo', '/quiet', '/optimize+', f'/out:{self.get_compiled_file()}', self._code]

    def get_compile_popen_kwargs(self) -> Dict[str, Any]:
        return {'stdout': subprocess.PIPE, 'stderr': subprocess.STDOUT}

    @classmethod
    def get_versionable_commands(cls) -> List[Tuple[str, str]]:
        return [('vbnc', cls.runtime_dict['mono-vbnc']), ('mono', cls.runtime_dict['mono'])]

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['/help'] if command == 'vbnc' else super().get_version_flags(command)

    @classmethod
    def get_find_first_mapping(cls) -> Optional[Dict[str, List[str]]]:
        res = super().get_find_first_mapping()
        if res:
            res['mono-vbnc'] = ['mono-vbnc', 'vbnc']
        return res
