from .php_executor import PHPExecutor


class Executor(PHPExecutor):
    name = 'PHP'
    command = 'php'
    command_paths = ['php5', 'php']
