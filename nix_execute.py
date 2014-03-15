import sys
import signal
import os
import time
import resource
import subprocess


class nix_Process(object):
    def __init__(self, chained):
        self._chained = chained
        self.stdout = chained.stdout
        self.stdin = chained.stdin
        self.usages = None
        self.returncode = None

    def __getattr__(self, name):
        if name in ["wait", "send_signal", "terminate", "kill"]:
            return getattr(self._chained, name)
        return object.__getattribute__(self, name)

    def poll(self):
        a = self._chained.poll()
        if a is not None:
            self.returncode = self._get_usages()[-1]
            return self.returncode
        return None

    def _get_usages(self):
        """
            Returns an array containing [bool tle, int max memory usage (kb), int runtime, int error code]
        """
        if not self.usages:
            self.usages = map(eval, self._chained.stderr.readline().split())
        return self.usages

    def get_execution_time(self):
        return self._get_usages()[2]

    def get_max_memory(self):
        return self._get_usages()[1]


def execute(path):
    print "Executing", path
    process = subprocess.Popen([sys.executable, __file__] + path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return nix_Process(process)


if __name__ == "__main__":
    child = sys.argv[1]
    args = sys.argv[1:]

    pid = None
    rusage = None
    code = None

    def sigchld(signum, frame):
        global code, rusage
        if pid is None:
            print 'Error'
            return
        _, code, rusage = os.wait4(pid, 0)

    h = signal.signal(signal.SIGCHLD, sigchld)
    pid = os.fork()
    if not pid:
        resource.setrlimit(resource.RLIMIT_AS, (32 * 1024 * 1024,) * 2)
        #resource.setrlimit(resource.RLIMIT_NOFILE, (4, 4))
        resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))

        os.dup2(1, 2)
        os.closerange(3, os.sysconf("SC_OPEN_MAX"))
        os.execvp(child, args)
        os._exit(3306)  # When you reach here, you are screwed
        # As much as being handed control of a MySQL server without
        # ANY SQL knowledge or docs. ENJOY.
    else:
        sys.stdin.close()
        sys.stdout.close()
        start = time.time()
        time.sleep(5)
        duration = time.time() - start
        signal.signal(signal.SIGCHLD, h)
        tle = 0
        if code is None:  # TLE
            os.kill(pid, signal.SIGKILL)
            _, code, rusage = os.wait4(pid, 0)
            tle = 1
        print>> sys.stderr, tle, rusage.ru_maxrss, duration, code
