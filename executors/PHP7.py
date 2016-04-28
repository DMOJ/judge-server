from .php_executor import PHPExecutor
from judgeenv import env


class Executor(PHPExecutor):
    name = 'PHP7'
    command = env['runtime'].get('php7')
    fs = ['.*\.so', '/etc/localtime$', '.*\.ini$']


initialize = Executor.initialize
