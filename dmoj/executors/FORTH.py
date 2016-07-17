from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    name = 'FORTH'
    command = 'gforth'
    command_paths = ['gforth']
    ext = '.fs'
    test_program = '''\
: HELLO  ( -- ) ." echo: Hello, World!" CR ;

HELLO
'''

    def get_cmdline(self):
        return [self.get_command(), self._code, '-e', 'bye']
