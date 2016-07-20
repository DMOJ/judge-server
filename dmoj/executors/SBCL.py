from dmoj.executors.base_executor import CompiledExecutor
from dmoj.executors.mixins import ScriptDirectoryMixin, NullStdoutMixin


class Executor(NullStdoutMixin, ScriptDirectoryMixin, CompiledExecutor):
    ext = '.cl'
    name = 'SBCL'
    command = 'sbcl'
    command_paths = ['sbcl']
    syscalls = ['personality', 'modify_ldt']
    fs = ['/dev/tty$', '/etc/nsswitch.conf$', '/etc/passwd$']
    test_program = '(write-line (read-line))'
    address_grace = 524288 + 131073 * 2<<8

    compile_script = '''(compile-file "{code}")'''

    def get_compile_args(self):
        return [self.get_command(), '--eval', self.compile_script.format(code=self._code), '--quit']

    def get_cmdline(self):
        return [self.get_command(), '--noinform', '--load', self.problem + ".fasl", '--quit', '--end-toplevel-options']

    def get_executable(self):
        return self.get_command()

    def get_security(self, *args, **kwargs):
        from dmoj.cptbox.syscalls import sys_readlink, sys_kill
        from dmoj.cptbox.handlers import ACCESS_DENIED

        sec = super(Executor, self).get_security(*args, **kwargs)
        old_readlink = sec[sys_readlink]

        # SBCL does something sketchy where it sets personality to no ASLR, and then re-execves itself.
        # However, if the read of /proc/self/exe is denied, it will continue execution.
        # Otherwise, we'd need to allow execve, personality, write on fd=3, poll, and kill.
        def new_readlink(debugger):
            if debugger.readstr(debugger.uarg0) == '/proc/self/exe':
                return ACCESS_DENIED(debugger)
            return old_readlink(debugger)

        sec[sys_readlink] = new_readlink
        sec[sys_kill] = lambda debugger: debugger.uarg0 == debugger.pid
        return sec
