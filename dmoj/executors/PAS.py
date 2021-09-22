from typing import List

from dmoj.cptbox import TracedPopen
from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.executors.base_executor import VersionFlags
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'pas'
    command = 'fpc'
    compiler_read_fs = [
        ExactFile('/etc/fpc.cfg'),
    ]
    compiler_time_limit = 20
    test_program = """\
var line : string;
begin
    readln(line);
    writeln(line);
end.
"""

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, '-Fe/dev/stderr', '-O2', self._code]

    def get_compile_output(self, process: TracedPopen) -> bytes:
        output = super().get_compile_output(process)
        return output if b'Fatal:' in output or b'Warning:' in output or b'Note:' in output else b''

    @classmethod
    def get_version_flags(cls, command: str) -> List[VersionFlags]:
        return ['-help']
