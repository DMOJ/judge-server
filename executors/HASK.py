from .base_executor import CompiledExecutor
from judgeenv import env


class Executor(CompiledExecutor):
    ext = '.hs'
    name = 'HASK'
    fs = ['.*\.so', '/usr/']
    command = env['runtime'].get('ghc')
    syscalls = ['getpid', 'getppid', 'clock_getres', 'timer_create', 'timer_settime',
                'timer_delete', 'newselect', 'select']
    test_program = '''\
main = do
    a <- getContents
    putStr a
'''

    def get_compile_args(self):
        return [self.get_command(), '-O', '-o', self.problem, self._code]


initialize = Executor.initialize
