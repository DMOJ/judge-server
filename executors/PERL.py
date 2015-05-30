from .base_executor import BaseExecutor
from judgeenv import env


class Executor(BaseExecutor):
    ext = '.pl'
    name = 'PERL'
    command = env['runtime'].get('perl')
    test_program = 'print<>'
    fs = ['.*\.(?:so|p[lm]$)', '/dev/urandom$']


initialize = Executor.initialize
