import sys
import os
import re
import errno
import subprocess
from collections import defaultdict

from cptbox import CHROOTSecurity, SecurePopen, PIPE, ALLOW
from cptbox.syscalls import *
from error import CompileError
from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env


CS_FS = ['.*\.so', '/proc/(?:self/|xen)', '/dev/shm/', '/proc/stat', '/usr/lib/mono',
         '/etc/nsswitch.conf$', '/etc/passwd$', '/etc/mono/', '/dev/null$', '.*/.mono/',
         '/sys/']
WRITE_FS = ['/proc/self/task/\d+/comm$']
UNLINK_FS = re.compile('/dev/shm/mono.\d+$')


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        source_code_file = self._file('%s.cs' % problem_id)
        self.name = self._file('%s.exe' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        csc_args = [env['runtime']['mono-csc'], source_code_file]
        csc_process = subprocess.Popen(csc_args, stderr=subprocess.PIPE, cwd=self._dir)
        _, compile_error = csc_process.communicate()
        if csc_process.returncode != 0:
            raise CompileError(compile_error)
        self.warning = compile_error

    def _get_security(self):
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

        sec[sys_open] = handle_open
        sec[sys_close] = handle_close
        sec[sys_dup2] = handle_dup
        sec[sys_dup3] = handle_dup
        sec[sys_write] = handle_write
        sec[sys_kill] = handle_kill
        sec[sys_tgkill] = handle_kill
        sec[sys_unlink] = unlink
        return sec

    def launch(self, *args, **kwargs):
        return SecurePopen(['mono', self.name] + list(args),
                           executable=env['runtime']['mono'],
                           security=self._get_security(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={}, cwd=self._dir, nproc=-1)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen(['mono', self.name] + list(args),
                                executable=env['runtime']['mono'],
                                env={},
                                cwd=self._dir,
                                **kwargs)


def initialize():
    if 'mono-csc' not in env['runtime'] or 'mono' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['mono-csc']):
        return False
    return test_executor('MONOCS', Executor, '''\
using System;

class test {
    public static void Main(string[] args) {
        Console.WriteLine("Hello, World!");
    }
}''')
