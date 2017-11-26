from dmoj.executors.mixins import ScriptDirectoryMixin
from .base_executor import ScriptExecutor


class Executor(ScriptDirectoryMixin, ScriptExecutor):
    ext = '.R'
    name = 'R'
    nproc = -1  # needs a bunch
    command = 'Rscript'
    test_program = 'writeLines(readLines(file("stdin")))'
    syscalls = ['setup', 'fork', 'waitpid', 'wait4', 'execve']

    fs = ['/etc/group$']

    def get_cmdline(self):
        return [self.get_command(), '--vanilla', self._code]
