from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.executors.mixins import NullStdoutMixin


class Executor(NullStdoutMixin, CompiledExecutor):
    ext = 'hs'
    name = 'HASK'
    command = 'ghc'
    syscalls = ['poll']
    test_program = '''\
main = do
    a <- getContents
    putStr a
'''

    def get_compile_args(self):
        return [self.get_command(), '-O2', '-o', self.problem, self._code]
