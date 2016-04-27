from .php_executor import PHPExecutor
from judgeenv import env


class Executor(PHPExecutor):
    name = 'PHP'
    command = env['runtime'].get('php')

    fs = PHPExecutor.fs
    if 'phpconfdir' in env['runtime']:
        fs += [env['runtime']['phpconfdir']]


initialize = Executor.initialize