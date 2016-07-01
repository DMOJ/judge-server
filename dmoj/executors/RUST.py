from .base_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = '.rs'
    name = 'RUST'
    fs = ['.*\.alias']
    command = env['runtime'].get('rustc')
    test_program = 'fn main() { println!("echo: Hello, World!"); }'

    def get_compile_args(self):
        return [self.get_command(), '-O', self._code]
