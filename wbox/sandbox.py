from _wbox import UserManager, ProcessManager
from subprocess import list2cmdline, Popen


class WBoxPopen(object):
    def __init__(self, argv, time, memory, nproc=1, executable=None, cwd=''):
        self.user = UserManager()
        self.process = ProcessManager(self.user.username, self.user.password)
        self.process.command = list2cmdline(argv)
        if executable is not None:
            self.process.executable = executable
        self.process.dir = cwd
        self.process.time = time
        self.process.memory = memory
        self.process.processes = nproc
        self.returncode = None

    def wait(self, timeout=None):
        self.process.wait(timeout)
        return self.poll()

    def poll(self):
        self.returncode = self.process.get_exit_code()
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
        raise NotImplementedError()

    @property
    def max_memory(self):
        raise NotImplementedError()

    @property
    def tle(self):
        raise NotImplementedError()

    @property
    def execution_time(self):
        raise NotImplementedError()

    @property
    def cpu_time(self):
        raise NotImplementedError()

    @property
    def r_execution_time(self):
        raise NotImplementedError()

    communicate = Popen.communicate
    _communicate = Popen._communicate
    _readerthread = Popen._readerthread
