from collections import defaultdict

from dmoj.cptbox.handlers import ALLOW, DISALLOW
from dmoj.cptbox.isolate import IsolateTracer
from dmoj.cptbox.syscalls import SYSCALL_COUNT
from dmoj.cptbox.tracer import PIPE, TracedPopen


class NullTracer(defaultdict):
    def __init__(self):
        for i in range(SYSCALL_COUNT):
            self[i] = ALLOW
