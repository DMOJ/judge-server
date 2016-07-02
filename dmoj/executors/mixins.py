import pty
import os


class NullStdoutMixin(object):
    def __init__(self, *args, **kwargs):
        self._devnull = open(os.devnull, 'w')
        super(NullStdoutMixin, self).__init__(*args, **kwargs)

    def cleanup(self):
        if hasattr(self, '_devnull'):
            self._devnull.close()
        super(NullStdoutMixin, self).cleanup()

    def get_compile_popen_kwargs(self):
        result = super(NullStdoutMixin, self).get_compile_popen_kwargs()
        result['stdout'] = self._devnull
        return result


class EmulateTerminalMixin(object):
    def get_compile_popen_kwargs(self):
        return {'stderr': self._slave, 'stdout': self._slave, 'stdin': self._slave}

    def get_compile_env(self):
        env = os.environ.copy()
        env['TERM'] = 'xterm'
        return env

    def get_compile_process(self):
        self._master, self._slave = pty.openpty()
        proc = super(EmulateTerminalMixin, self).get_compile_process()

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
