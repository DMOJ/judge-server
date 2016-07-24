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
    """
    Some languages may insist on providing certain functionality (e.g. colored highlighting of errors) if they feel
    they are connected to a terminal. Some are more persistent than others in enforcing this, so this mixin aims
    to provide a convincing-enough lie to the runtime so that it starts singing in color.
    """
    if os.name != 'nt':
        def get_compile_process(self):
            """
            Creates a compiler process with the stderr stream swapped for a master pty opened for read.
            """

            import pty

            self._master, self._slave = pty.openpty()
            proc = super(EmulateTerminalMixin, self).get_compile_process()

            class io_error_wrapper(object):
                """
                Wrap pty-related IO errors so that we don't crash Popen.communicate()
                """

                def __init__(self, fd):
                    self.fd = fd

                def read(self, *args, **kwargs):
                    try:
                        return self.fd.read(*args, **kwargs)
                    except (IOError, OSError):
                        return ''

                def __getattr__(self, attr):
                    return getattr(self.fd, attr)

            # Since stderr and stdout are connected to the same slave pty, proc.stderr will contain the merged stdout
            # of the process as well.
            proc.stderr = io_error_wrapper(os.fdopen(self._master, 'r'))

            os.close(self._slave)
            return proc

        def get_compile_popen_kwargs(self):
            """
            Emulate the streams of a process connected to a terminal: stdin, stdout, and stderr are all ptys.
            """
            return {'stdin': self._slave, 'stdout': self._slave, 'stderr': self._slave}

        def get_compile_env(self):
            """
            Some runtimes *cough cough* Swift *cough cough* actually check the environment variables too.
            """
            env = super(EmulateTerminalMixin, self).get_compile_env() or os.environ.copy()
            env['TERM'] = 'xterm'
            return env


class ScriptDirectoryMixin(object):
    """Certain script executors need access to the entire directory of the script,
    usually for some searching purposes."""

    def get_fs(self):
        return super(ScriptDirectoryMixin, self).get_fs() + [self._dir]
