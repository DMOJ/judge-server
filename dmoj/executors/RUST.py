from .base_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = '.rs'
    name = 'RUST'
    fs = ['.*\.alias', '.*\.so', '/usr/', '/etc/localtime$', '/dev/null$', '/sys/devices/system/cpu/online$', '/proc/stat$', '/proc/self/maps$']
    command = env['runtime'].get('rustc')
    syscalls = ['sched_getaffinity', 'madvise']
    test_program = 'fn main() { println!("echo: Hello, World!"); }'

    def get_compile_args(self):
        return [self.get_command(), self._code]


initialize = Executor.initialize
