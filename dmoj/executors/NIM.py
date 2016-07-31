from .base_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = '.nim'
    name = 'NIM'
    command = 'nim'
    test_program = '''\
echo readLine(stdin)
'''

    def get_compile_args(self):
        return [self.get_command(), 'c', '--verbosity:0', self._code]
