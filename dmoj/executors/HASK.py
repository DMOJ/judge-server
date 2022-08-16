from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'hs'
    command = 'ghc'
    compiler_read_fs = [
        RecursiveDir('/proc/self/task'),
        RecursiveDir('/var/lib/ghc'),
    ]

    test_program = """\
main = do
    a <- getContents
    putStr a
"""

    def get_compile_args(self):
        return [self.get_command(), '-O2', '-o', self.problem, self._code]
