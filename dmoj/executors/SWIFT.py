from dmoj.cptbox.filesystem_policies import RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'swift'
    command = 'swiftc'
    compiler_read_fs = [
        RecursiveDir('~/.cache'),
    ]
    compiler_write_fs = compiler_read_fs
    test_program = 'print(readLine()!)'

    def get_compile_args(self):
        return [self.get_command(), self._code]
