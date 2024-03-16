from typing import List

from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.executors.mixins import NullStdoutMixin


class Executor(NullStdoutMixin, CompiledExecutor):
    ext = 'hs'
    command = 'ghc'
    compiler_read_fs = [
        RecursiveDir('/proc/self/task'),
        RecursiveDir('/var/lib/ghc'),
    ]
    syscalls = ['pselect6', 'timerfd_settime']
    nproc = -1

    test_program = """\
main = do
    a <- getContents
    putStr a
"""

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, '-O2', '-o', self.problem, self._code]
