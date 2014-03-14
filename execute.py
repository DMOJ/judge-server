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
    os.execvp(child, args)
else:
    start = time.time()
    time.sleep(5)
    duration = time.time() - start
    signal.signal(signal.SIGCHLD, h)
    if code is None: # TLE
        os.kill(pid, signal.SIGKILL)
        _, code, rusage = os.wait4(pid, 0)
        print 'Time Limit Exceeded'
    print rusage.ru_maxrss, 'KB of RAM'
    print 'Execution time: %.3f seconds' % duration
    print 'Return:', code
