from .base_executor import CompiledExecutor
from judgeenv import env


class Executor(CompiledExecutor):
    ext = '.hs'
    name = 'HASK'
    command = env['runtime'].get('ghc')
    syscalls = ['getpid', 'getppid', 'clock_getres', 'timer_create', 'timer_settime',
                'timer_delete', 'sys_newselect']
    test_program = '''\
main = do
    a <- getContents
    putStr a
'''


initialize = Executor.initialize
