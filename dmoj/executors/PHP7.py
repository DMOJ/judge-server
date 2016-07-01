from .php_executor import PHPExecutor
from dmoj.judgeenv import env


class Executor(PHPExecutor):
    name = 'PHP7'
    command = 'php7'
    fs = ['.*\.ini$']
