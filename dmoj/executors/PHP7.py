from .php_executor import PHPExecutor


class Executor(PHPExecutor):
    name = 'PHP7'
    command = 'php7'
    command_paths = ['php7']
    fs = ['.*\.ini$']
