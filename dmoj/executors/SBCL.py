from dmoj.executors.compiled_executor import CompiledExecutor
from dmoj.executors.mixins import NullStdoutMixin


# SBCL implements its own heap management, and relies on ASLR being disabled. So, on startup,
# it reads /proc/self/exe do determine if ASLR is disabled. If not, it forks, sets
# personality (http://man7.org/linux/man-pages/man2/personality.2.html) to disable ASLR,
# then execve's itself...
# As of https://github.com/DMOJ/judge/issues/277 we set personality ourselves to disable ASLR,
# so allowing (or blocking) the execve hack is not necessary: SBCL detects that ASLR is disabled,
# and proceeds to run.
class Executor(NullStdoutMixin, CompiledExecutor):
    ext = 'cl'
    command = 'sbcl'
    syscalls = ['personality']
    test_program = '(write-line (read-line))'
    address_grace = 262144
    data_grace = 262144
    nproc = -1

    compile_script = """(compile-file "{code}")"""

    def get_compile_args(self):
        return [self.get_command(), '--eval', self.compile_script.format(code=self._code), '--quit']

    def get_cmdline(self, **kwargs):
        return [
            self.get_command(),
            '--dynamic-space-size',
            str(int(kwargs['memory'] / 1024.0 + 1)),
            '--noinform',
            '--no-sysinit',
            '--no-userinit',
            '--load',
            self.problem + '.fasl',
            '--quit',
            '--end-toplevel-options',
        ]

    def get_executable(self):
        return self.get_command()
