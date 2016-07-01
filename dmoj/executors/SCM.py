from .base_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = '.scm'
    name = 'SCM'
    command = env['runtime'].get('chicken-csc')
    syscalls = ['newselect', 'select']
    test_program = '(declare (uses extras)) (map print (read-lines))'

    def get_compile_args(self):
        return [self.get_command(), self._code]
