from collections import defaultdict

from dmoj.cptbox.sandbox import SecurePopen, PIPE
from dmoj.cptbox.handlers import DISALLOW, ALLOW
from dmoj.cptbox.chroot import CHROOTSecurity
from dmoj.cptbox.syscalls import SYSCALL_COUNT

if sys.version_info.major == 2:
    range = xrange

class NullSecurity(defaultdict):
    def __init__(self):
        for i in range(SYSCALL_COUNT):
            self[i] = ALLOW
