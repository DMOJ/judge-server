from __future__ import print_function

import errno
import logging
import os
import re
import sys
from collections import defaultdict

from dmoj.cptbox import CHROOTSecurity, SecurePopen
from dmoj.cptbox.handlers import ALLOW, ACCESS_DENIED
from dmoj.cptbox.syscalls import *
from .base_executor import CompiledExecutor

WRITE_FS = ['/proc/self/task/\d+/comm$', '.*?/mono\.\d+$']
UNLINK_FS = re.compile('.*?/mono.\d+$')

log = logging.getLogger('dmoj.security')


class MonoSecurePopen(SecurePopen):
    def _cpu_time_exceeded(self):
        pass


class MonoExecutor(CompiledExecutor):
    name = 'MONO'
    nproc = -1  # If you use Mono on Windows you are doing it wrong.
    address_grace = 262144
    cptbox_popen_class = MonoSecurePopen
    fs = ['/proc/(?:self/|xen)', '/dev/shm', '/proc/stat', 'mono',
          '/etc/mono/', '.*/.mono/', '/sys/', '/proc/uptime$', '.*?/mono.\d+$']

    def get_compiled_file(self):
        return self._file('%s.exe' % self.problem)

    def get_cmdline(self):
        return ['mono', self._executable]

    def get_executable(self):
        return self.runtime_dict['mono']

    def get_security(self, launch_kwargs=None):
        fs = self.get_fs() + [self._dir]
        sec = CHROOTSecurity(fs, io_redirects=launch_kwargs.get('io_redirects', None))
        sec[sys_sched_getaffinity] = ALLOW
        sec[sys_sched_setscheduler] = ALLOW
        sec[sys_ftruncate64] = ALLOW
        sec[sys_sched_yield] = ALLOW
        sec[sys_rt_sigsuspend] = ALLOW
        sec[sys_wait4] = ALLOW

        fs = sec.fs_jail
        write_fs = re.compile('|'.join(WRITE_FS))
        writable = defaultdict(bool)
        writable[1] = writable[2] = True

        def handle_open(debugger):
            file = debugger.readstr(debugger.uarg0)
            if fs.match(file) is None:
                print('Not allowed to access:', file, file=sys.stderr)
                log.warning('Denied file open: %s', file)
                return False
            can = write_fs.match(file) is not None

            def update():
                writable[debugger.result] = can
            debugger.on_return(update)
            return True

        def handle_close(debugger):
            writable[debugger.arg0] = False
            return True

        def handle_dup(debugger):
            writable[debugger.arg1] = writable[debugger.arg0]
            return True

        def handle_write(debugger):
            return writable[debugger.arg0]

        def handle_ftruncate(debugger):
            return writable[debugger.arg0]

        def handle_kill(debugger):
            # Mono likes to signal other instances of it, but doesn't care if it fails.
            def kill_return():
                debugger.result = -errno.EPERM
            if debugger.arg0 != debugger.pid:
                debugger.syscall = debugger.getpid_syscall
                debugger.on_return(kill_return)
            return True

        def unlink(debugger):
            path = debugger.readstr(debugger.uarg0)
            if UNLINK_FS.match(path) is None:
                print('Not allowed to unlink:', path)
                log.warning('Denied file unlink: %s', path)
                return False
            return True

        sec[sys_open] = sec[sys_shm_open] = handle_open
        sec[sys_close] = handle_close
        sec[sys_dup2] = handle_dup
        sec[sys_dup3] = handle_dup
        sec[sys_write] = handle_write
        sec[sys_ftruncate] = handle_ftruncate
        sec[sys_kill] = handle_kill
        sec[sys_tgkill] = handle_kill
        sec[sys_unlink] = sec[sys_shm_unlink] = unlink
        sec[sys_socket] = ACCESS_DENIED
        sec[sys_socketcall] = ACCESS_DENIED
        return sec

    @classmethod
    def get_find_first_mapping(cls):
        res = super(MonoExecutor, cls).get_find_first_mapping()
        res['mono'] = ['mono']
        return res

    @classmethod
    def initialize(cls, sandbox=True):
        if 'mono' not in cls.runtime_dict or not os.path.isfile(cls.runtime_dict['mono']):
            return False
        return super(MonoExecutor, cls).initialize(sandbox=sandbox)
