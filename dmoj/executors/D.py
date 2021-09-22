from typing import List

from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'd'
    address_grace = 32768
    command = 'dmd'
    compiler_read_fs = [
        ExactFile('/etc/dmd.conf'),
    ]
    test_program = """\
import std.stdio;

void main() {
    writeln(readln());
}
"""
    source_filename_format = 'main.{ext}'

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, '-O', '-inline', '-release', '-w', self._code, f'-of{self.problem}']
