from typing import List

from dmoj.cptbox.filesystem_policies import ExactFile, RecursiveDir
from dmoj.executors.compiled_executor import CompiledExecutor


# Running Dart normally results in unholy memory usage
# Thankfully compiling it results in something... far more sane
class Executor(CompiledExecutor):
    ext = 'dart'
    nproc = -1  # Dart uses a really, really large number of threads
    command = 'dart'
    compiler_read_fs = [
        # Dart shells out...
        ExactFile('/bin/sh'),
        RecursiveDir('/proc/self/fd'),
    ]
    test_program = """
void main() {
    print("echo: Hello, World!");
}
"""
    address_grace = 512 * 1024

    syscalls = [
        'timerfd_settime',
        'memfd_create',
        'msync',
        'ftruncate',
    ]

    def get_compile_args(self) -> List[str]:
        command = self.get_command()
        assert command is not None
        assert self._code is not None
        return [command, f'--snapshot={self.get_compiled_file()}', self._code]

    def get_cmdline(self, **kwargs) -> List[str]:
        command = self.get_command()
        assert command is not None
        return [command, self.get_compiled_file()]

    def get_executable(self):
        return self.get_command()
