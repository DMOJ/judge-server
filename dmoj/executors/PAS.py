from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.executors.mixins import NullStdoutMixin


class Executor(NullStdoutMixin, CompiledExecutor):
    ext = 'pas'
    name = 'PAS'
    command = 'fpc'
    compiler_read_fs = [
        ExactFile('/etc/fpc.cfg'),
    ]
    test_program = """\
var line : string;
begin
    readln(line);
    writeln(line);
end.
"""

    def get_compile_args(self):
        return [self.get_command(), '-Fe/dev/stderr', '-O2', self._code]

    def get_compile_output(self, process):
        output = super().get_compile_output(process)
        return output if b'Fatal:' in output or b'Warning:' in output or b'Note:' in output else ''

    @classmethod
    def get_version_flags(cls, command):
        return ['-help']
