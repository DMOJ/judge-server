import os
import sys
from shutil import copyfile

from dmoj.judgeenv import env
from dmoj.utils.unicode import utf8bytes

try:
    if os.name == 'nt':
        from dmoj.wbox import WBoxPopen, default_inject32, default_inject64, default_inject_func


        class PlatformExecutorMixin(object):
            inject32 = env.inject32 or default_inject32
            inject64 = env.inject64 or default_inject64
            inject_func = env.inject_func or default_inject_func
            network_block = True

            def get_env(self):
                return None

            def get_network_block(self):
                return self.network_block

            def get_inject32(self):
                file = self._file('dmsec32.dll')
                copyfile(self.inject32, file)
                return file

            def get_inject64(self):
                file = self._file('dmsec64.dll')
                copyfile(self.inject64, file)
                return file

            def get_inject_func(self):
                return self.inject_func

            def launch(self, *args, **kwargs):
                return WBoxPopen(self.get_cmdline() + list(args),
                                 time=kwargs.get('time'), memory=kwargs.get('memory'),
                                 cwd=self._dir, executable=self.get_executable(),
                                 network_block=True, env=self.get_env(),
                                 nproc=self.get_nproc() + 1,
                                 inject32=self.get_inject32(),
                                 inject64=self.get_inject64(),
                                 inject_func=self.get_inject_func())
    else:
        from dmoj.cptbox import SecurePopen, PIPE, CHROOTSecurity, syscalls
        from dmoj.cptbox.handlers import ALLOW

        BASE_FILESYSTEM = ['/dev/(?:null|tty|zero|u?random)$',
                           '/usr/(?!home)', '/lib(?:32|64)?/', '/opt/',
                           '/etc/(?:localtime|timezone|nsswitch.conf|resolv.conf|passwd)$',
                           '/$']

        if 'freebsd' in sys.platform:
            BASE_FILESYSTEM += [r'/etc/s?pwd\.db$', '/dev/hv_tsc$']
        else:
            BASE_FILESYSTEM += ['/sys/devices/system/cpu(?:$|/online)',
                                '/etc/selinux/config$']

        if sys.platform.startswith('freebsd'):
            BASE_FILESYSTEM += [r'/etc/libmap\.conf$', r'/var/run/ld-elf\.so\.hints$']
        else:
            # Linux and kFreeBSD mounts linux-style procfs.
            BASE_FILESYSTEM += ['/proc/self/(?:maps|exe|auxv)$', '/proc/self$',
                                '/proc/(?:meminfo|stat|cpuinfo|filesystems)$',
                                '/proc/sys/vm/overcommit_memory$']

            # Linux-style ld.
            BASE_FILESYSTEM += [r'/etc/ld\.so\.(?:nohwcap|preload|cache)$']


        class PlatformExecutorMixin(object):
            address_grace = 65536
            personality = 0x0040000  # ADDR_NO_RANDOMIZE
            fs = []
            syscalls = []

            def _add_syscalls(self, sec):
                for name in self.get_allowed_syscalls():
                    if isinstance(name, tuple) and len(name) == 2:
                        name, handler = name
                    else:
                        handler = ALLOW
                    sec[getattr(syscalls, 'sys_' + name)] = handler
                return sec

            def get_security(self, launch_kwargs=None):
                if CHROOTSecurity is None:
                    raise NotImplementedError('No security manager on Windows')
                sec = CHROOTSecurity(self.get_fs(), io_redirects=launch_kwargs.get('io_redirects', None))
                return self._add_syscalls(sec)

            def get_fs(self):
                name = self.get_executor_name()
                return BASE_FILESYSTEM + self.fs + env.get('extra_fs', {}).get(name, [])

            def get_allowed_syscalls(self):
                return self.syscalls

            def get_address_grace(self):
                return self.address_grace

            def get_env(self):
                return {'LANG': 'C'}

            def launch(self, *args, **kwargs):
                return SecurePopen([utf8bytes(a) for a in self.get_cmdline() + list(args)],
                                   executable=utf8bytes(self.get_executable()),
                                   security=self.get_security(launch_kwargs=kwargs),
                                   address_grace=self.get_address_grace(),
                                   personality=self.personality,
                                   time=kwargs.get('time'), memory=kwargs.get('memory'),
                                   wall_time=kwargs.get('wall_time'),
                                   stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                                   env=self.get_env(), cwd=utf8bytes(self._dir), nproc=self.get_nproc(),
                                   unbuffered=kwargs.get('unbuffered', False))
except ImportError:
    pass


class NullStdoutMixin(object):
    """
    Some compilers print a lot of debug info to stdout even with successful compiles. This mixin pipes that generally-
    useless data into os.devnull so that the user never sees it.
    """

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
    """
    Certain script executors need access to the entire directory of the script,
    usually for some searching purposes.
    """

    def get_fs(self):
        return super(ScriptDirectoryMixin, self).get_fs() + [self._dir]
