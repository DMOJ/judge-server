from collections import defaultdict

from dmoj.cptbox.chroot import CHROOTSecurity
from dmoj.cptbox.handlers import ALLOW, DISALLOW
from dmoj.cptbox.sandbox import PIPE, SecurePopen
from dmoj.cptbox.syscalls import SYSCALL_COUNT


class NullSecurity(defaultdict):
    def __init__(self):
        for i in range(SYSCALL_COUNT):
            self[i] = ALLOW
