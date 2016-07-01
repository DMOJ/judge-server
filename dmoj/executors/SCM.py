from .base_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = '.scm'
    name = 'SCM'
    command = 'chicken-csc'
    syscalls = ['newselect', 'select']
    test_program = '(declare (uses extras)) (map print (read-lines))'

    def get_compile_args(self):
        return [self.get_command(), self._code]
