import sys
import signal
import os
import time
import resource

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
    resource.setrlimit(resource.RLIMIT_AS, (32*1024*1024,)*2)
    #resource.setrlimit(resource.RLIMIT_NOFILE, (4, 4))
    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
    os.dup2(os.open('/dev/null', os.O_WRONLY), 2)
    os.execvp(child, args)
    os._exit(3306) # When you reach here, you are screwed
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
    if code is None: # TLE
        os.kill(pid, signal.SIGKILL)
        _, code, rusage = os.wait4(pid, 0)
        tle = 1
    print>>sys.stderr, tle, rusage.ru_maxrss, duration, code
