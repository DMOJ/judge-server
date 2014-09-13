import os
from platform import architecture
import threading
import time
from _cptbox import Process, SYSCALL_COUNT

DISALLOW = 0
ALLOW = 1
_CALLBACK = 2

PIPE = object()


def _find_exe(path):
    if os.path.isabs(path):
        return path
    if os.sep in path:
        return os.path.abspath(path)
    for dir in os.environ.get('PATH', os.defpath).split(os.pathsep):
        p = os.path.join(dir, path)
        if os.access(p, os.X_OK):
            return p
    raise OSError()


class _SecurePopen(Process):
    def __init__(self, bitness, args, executable=None, security=None, time=0, memory=0, stdin=PIPE, stdout=PIPE, stderr=None, env=()):
        self._bitness = bitness
        self._executable = executable or _find_exe(args[0])
        self._args = args
        self._env = env
        self._time = time
        self._memory = memory
        self._tle = False
        self.__init_streams(stdin, stdout, stderr)

        self._security = security
        self._callbacks = [None] * SYSCALL_COUNT
        if security is None:
            for i in xrange(SYSCALL_COUNT):
                self._handler(i, ALLOW)
        else:
            for i in xrange(SYSCALL_COUNT):
                handler = security.get(i, DISALLOW)
                if not isinstance(handler, int):
                    if not callable(handler):
                        raise ValueError('Handler not callable: ' + handler)
                    self._callbacks[i] = handler
                    handler = _CALLBACK
                self._handler(i, handler)

        self._started = threading.Event()
        self._died = threading.Event()
        self._worker = threading.Thread(target=self._run_process)
        self._worker.start()
        if time:
            # Spawn thread to kill process after it times out
            self._shocker = threading.Thread(target=self._shocker_thread)
            self._shocker.start()

    def wait(self):
        self._died.wait()
        return self.returncode

    def poll(self):
        return self.returncode

    @property
    def mle(self):
        return self._memory is not None and self.max_memory > self._memory

    @property
    def tle(self):
        return self._tle

    @property
    def bitness(self):
        return self._bitness

    def kill(self):
        os.kill(self.pid, os.SIGKILL)

    def _callback(self, syscall):
        callback = self._callbacks[syscall]
        if callback is not None:
            return callback(self._debugger)
        return False

    def _run_process(self):
        self._spawn(self._executable, self._args, self._env)
        self._started.set()
        code = self._monitor()

        if self._time and self.execution_time > self._time:
            self._tle = True
        self._died.set()
        return code

    def _shocker_thread(self):
        self._started.wait()

        while not self._exited:
            if self.execution_time > self._time:
                os.kill(self.pid, os.SIGKILL)
                self._tle = True
                break
            time.sleep(1)

    def __init_streams(self, stdin, stdout, stderr):
        if stdin is PIPE:
            self._child_stdin, self._stdin = os.pipe()
            self.stdin = os.fdopen(self._stdin, 'w')
        elif isinstance(stdin, int):
            self._child_stdin, self._stdin = stdin, -1
        elif stdin is not None:
            self._child_stdin, self._stdin = stdin.fileno(), -1
        else:
            self._child_stdin = self._stdin = -1

        if stdout is PIPE:
            self._stdout, self._child_stdout = os.pipe()
            self.stdout = os.fdopen(self._stdout, 'r')
        elif isinstance(stdout, int):
            self._stdout, self._child_stdout = -1, stdout
        elif stdout is not None:
            self._stdout, self._child_stdout = -1, stdout.fileno()
        else:
            self._stdout = self._child_stdout = -1

        if stderr is PIPE:
            self._stderr, self._child_stderr = os.pipe()
            self.stderr = os.fdopen(self._stderr, 'r')
        elif isinstance(stderr, int):
            self._stderr, self._child_stderr = -1, stderr
        elif stderr is not None:
            self._stderr, self._child_stderr = -1, stderr.fileno()
        else:
            self._stderr = self._child_stderr = -1
        

def SecurePopen(argv, executable=None, *args, **kwargs):
    executable = executable or _find_exe(argv[0])
    bitness = int(architecture(executable)[0][:2])
    return _SecurePopen(bitness, argv, executable, *args, **kwargs)