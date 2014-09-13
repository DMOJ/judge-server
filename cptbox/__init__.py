from collections import defaultdict
from .sandbox import SecurePopen, DISALLOW, ALLOW
from .chroot import CHROOTSecurity


class NullSecurity(defaultdict):
    def __init__(self):
        super(NullSecurity, self).__init__(lambda: ALLOW)
