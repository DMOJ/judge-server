from _wbox import UserManager, ProcessManager, NetworkManager
from subprocess import list2cmdline, Popen
from winutils import execution_time
from uuid import uuid1


class WBoxPopen(object):
    def __init__(self, argv, time, memory, nproc=1, executable=None, cwd=None, env=None, network_block=False):
        self.user = UserManager()
        self.process = ProcessManager(self.user.username, self.user.password)
        argv = list2cmdline(argv)
        if not isinstance(argv, unicode):
            argv = argv.decode('mbcs')
        self.process.command = argv
        if executable is not None:
            if not isinstance(executable, unicode):
                executable = executable.decode('mbcs')
            self.process.executable = executable
        if cwd is not None:
            if not isinstance(cwd, unicode):
                cwd = cwd.decode('mbcs')
            self.process.dir = cwd
        if env is not None:
            self.process.set_environment(self._encode_environment(env))
        self.process.time_limit = time
        self.process.memory_limit = memory * 1024
        self.process.process_limit = nproc
        self.returncode = None
        self.universal_newlines = False
        if executable is not None and network_block:
            self.network_block = NetworkManager('wbox_%s' % uuid1(), executable)
        else:
            self.network_block = None
        self.process.spawn()

    @staticmethod
    def _encode_environment(env):
        buf = []
        for key, value in env.iteritems():
            if not isinstance(key, unicode):
                key = key.decode('mbcs')
            if not isinstance(value, unicode):
                value = value.decode('mbcs')
            buf.append(u'%s=%s' % (key, value))
        return u'\0'.join(buf) + u'\0\0'

    def wait(self, timeout=None):
        self.process.wait(timeout)
        return self.poll()

    def poll(self):
        self.returncode = self.process.get_exit_code()
        if self.returncode is not None and self.network_block is not None:
            self.network_block.dispose()
        return self.returncode

    def kill(self, code=0xDEADBEEF):
        self.process.terminate(code)

    @property
    def stdin(self):
        return self.process.stdin

    @property
    def stdout(self):
        return self.process.stdout

    @property
    def stderr(self):
        return self.process.stderr

    @property
    def mle(self):
        return self.process.mle

    @property
    def max_memory(self):
        return self.process.memory / 1024.

    @property
    def max_memory_bytes(self):
        return self.process.memory

    @property
    def tle(self):
        return self.process.tle

    @property
    def execution_time(self):
        return self.process.execution_time

    @property
    def cpu_time(self):
        return execution_time(self.process._handle)

    @property
    def r_execution_time(self):
        return self.process.execution_time

    def communicate(self, stdin=None):
        return self._communicate(stdin)

    _communicate = Popen._communicate.im_func
    _readerthread = Popen._readerthread.im_func
