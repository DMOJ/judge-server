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
    address_grace = 128 * 1024

    syscalls = [
        'timerfd_settime',
        'memfd_create',
        'msync',
        'ftruncate',
    ]

    def get_compile_args(self):
        return [self.get_command(), '--snapshot=%s' % self.get_compiled_file(), self._code]

    def get_cmdline(self, **kwargs):
        return [self.get_command(), self.get_compiled_file()]

    def get_executable(self):
        return self.get_command()
