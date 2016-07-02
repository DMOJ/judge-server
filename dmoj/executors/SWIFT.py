import os
import pty

from .base_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = '.swift'
    name = 'SWIFT'
    command = 'swiftc'
    test_program = 'print(readLine()!)'

    def get_compile_args(self):
        return [self.get_command(), self._code]

    def get_compile_popen_kwargs(self):
        return {'stderr': self._slave, 'stdout': self._slave, 'stdin': self._slave}

    def get_compile_env(self):
        env = os.environ.copy()
        env['TERM'] = 'xterm'
        return env

    def get_compile_process(self):
        self._master, self._slave = pty.openpty()
        proc = super(Executor, self).get_compile_process()

        class io_error_wrapper(object):
            def __init__(self, fd):
                self.fd = fd

            def read(self, *args, **kwargs):
                try:
                    return self.fd.read(*args, **kwargs)
                except (IOError, OSError):
                    return ''

            def __getattr__(self, attr):
                return getattr(self.fd, attr)

        proc.stderr = io_error_wrapper(os.fdopen(self._master, 'r'))

        os.close(self._slave)
        return proc
