from dmoj.cptbox.filesystem_policies import ExactFile, RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'swift'
    command = 'swiftc'
    compiler_read_fs = [
        RecursiveDir('~/.cache'),
        ExactFile('/proc/self/cmdline'),
    ]
    compiler_write_fs = [
        RecursiveDir('~/.cache'),
    ]
    compiler_required_dirs = ['~/.cache']
    test_program = 'print(readLine()!)'

    def get_compile_args(self):
        return [self.get_command(), self._code]
