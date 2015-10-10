import sys
import os
import re
import errno
from collections import defaultdict

from cptbox import CHROOTSecurity, ALLOW
from cptbox.syscalls import *
from .base_executor import CompiledExecutor
from judgeenv import env


CS_FS = ['.*\.so', '/proc/(?:self/|xen)', '/dev/shm/', '/proc/stat', '/usr/lib/mono',
         '/etc/nsswitch.conf$', '/etc/passwd$', '/etc/mono/', '/dev/null$', '.*/.mono/',
         '/sys/']
WRITE_FS = ['/proc/self/task/\d+/comm$', '/dev/shm/mono\.\d+$']
UNLINK_FS = re.compile('/dev/shm/mono.\d+$')


class MonoExecutor(CompiledExecutor):
    name = 'MONO'
    nproc = -1  # If you use Mono on Windows you are doing it wrong.

    def get_compiled_file(self):
        return self._file('%s.exe' % self.problem)

    def get_cmdline(self):
        return ['mono', self._executable]

    def get_executable(self):
        return env['runtime']['mono']

    def get_security(self):
        fs = CS_FS + [self._dir]
        sec = CHROOTSecurity(fs)
        sec[sys_sched_getaffinity] = ALLOW
        sec[sys_statfs] = ALLOW
        sec[sys_ftruncate64] = ALLOW
        sec[sys_clock_getres] = ALLOW
        sec[sys_socketcall] = ALLOW
        sec[sys_sched_yield] = ALLOW

        fs = sec.fs_jail
        write_fs = re.compile('|'.join(WRITE_FS))
        writable = defaultdict(bool)
        writable[1] = writable[2] = True

        def handle_open(debugger):
            file = debugger.readstr(debugger.uarg0)
            if fs.match(file) is None:
                print>>sys.stderr, 'Not allowed to access:', file
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
                print 'Not allowed to unlink:', UNLINK_FS
                return False
            return True

        def handle_socket(debugger):
            def socket_return():
                debugger.result = -errno.EACCES
            debugger.syscall = debugger.getpid_syscall
            debugger.on_return(socket_return)
            return True

        sec[sys_open] = handle_open
        sec[sys_close] = handle_close
        sec[sys_dup2] = handle_dup
        sec[sys_dup3] = handle_dup
        sec[sys_write] = handle_write
        sec[sys_ftruncate] = handle_ftruncate
        sec[sys_kill] = handle_kill
        sec[sys_tgkill] = handle_kill
        sec[sys_unlink] = unlink
        sec[sys_socket] = handle_socket
        return sec

    @classmethod
    def initialize(cls, sandbox=True):
        if 'mono' not in env['runtime'] or not os.path.isfile(env['runtime']['mono']):
            return False
        return super(MonoExecutor, cls).initialize(sandbox=sandbox)
