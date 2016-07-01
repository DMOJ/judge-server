from dmoj.executors.base_executor import CompiledExecutor
from dmoj.executors.mixins import NullStdoutMixin
from dmoj.judgeenv import env


class Executor(NullStdoutMixin, CompiledExecutor):
    ext = '.hs'
    name = 'HASK'
    command = env['runtime'].get('ghc')
    syscalls = ['newselect', 'select']
    test_program = '''\
main = do
    a <- getContents
    putStr a
'''

    def get_compile_args(self):
        return [self.get_command(), '-O', '-o', self.problem, self._code]
