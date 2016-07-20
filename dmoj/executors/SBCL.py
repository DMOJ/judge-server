from dmoj.executors.base_executor import CompiledExecutor
from dmoj.executors.mixins import ScriptDirectoryMixin, NullStdoutMixin


class Executor(NullStdoutMixin, ScriptDirectoryMixin, CompiledExecutor):
    ext = '.cl'
    name = 'SBCL'
    command = 'sbcl'
    command_paths = ['sbcl']
    fs = ['/dev/tty$', '/etc/nsswitch.conf$', '/etc/passwd$']
    address_grace = 524288 + 262146  # 512mb so that it starts, + 256mb so that the GC doesn't die
    
    test_program = '(write-line (read-line))'

    compile_script = '''(compile-file "{code}")'''

    def get_compile_args(self):
        return [self.get_command(), '--eval', self.compile_script.format(code=self._code), '--quit']

    def get_cmdline(self):
        return [self.get_command(), '--noinform', '--load', self.problem + ".fasl", '--quit', '--end-toplevel-options']

    def get_executable(self):
        return self.get_command()

    def get_security(self, *args, **kwargs):
        from dmoj.cptbox.syscalls import sys_open
        from dmoj.cptbox.handlers import ACCESS_DENIED

        sec = super(Executor, self).get_security(*args, **kwargs)
        old_open = sec[sys_open]

        # SBCL does something sketchy where it sets personality to no ASLR, and then re-execves itself.
        # However, if the read of /proc/self/exe is denied, it will continue execution.
        # Otherwise, we'd need to allow execve, personality,, write on fd=3, poll, and kill.
        def new_open(debugger):
            if debugger.readstr(debugger.uarg0) == '/proc/self/exe':
                return ACCESS_DENIED(debugger)
            return old_open(debugger)

        sec[sys_open] = new_open

