from collections import defaultdict

from .sandbox import SecurePopen, DISALLOW, ALLOW, PIPE
from .chroot import CHROOTSecurity
from dmoj.cptbox.syscalls import SYSCALL_COUNT


class NullSecurity(defaultdict):
    def __init__(self):
        for i in xrange(SYSCALL_COUNT):
            self[i] = ALLOW
