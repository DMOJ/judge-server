import os
import re
import subprocess

from cptbox import CHROOTSecurity, SecurePopen, PIPE, ALLOW
from cptbox.syscalls import *
from error import CompileError
from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

CS_FS = ['.*\.so', '/proc/(?:self/|xen)', '/dev/shm/', '/proc/stat', '/usr/lib/mono/',
         '/etc/nsswitch.conf$', '/etc/passwd$', '/etc/mono/', '/dev/null$', '.*/.mono/',
         '/sys/']
UNLINK_FS = re.compile('/dev/shm/mono.\d+$')


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        source_code_file = self._file('%s.cs' % problem_id)
        self.name = self._file('%s.exe' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        csc_args = [env['runtime']['csc'], source_code_file]
        csc_process = subprocess.Popen(csc_args, stderr=subprocess.PIPE, cwd=self._dir)
        _, compile_error = csc_process.communicate()
        if csc_process.returncode != 0:
            raise CompileError(compile_error)
        self.warning = compile_error

    def _get_security(self):
        sec = CHROOTSecurity(CS_FS + [self._dir], writable=(1, 2, 3))
        sec[sys_sched_getaffinity] = ALLOW
        sec[sys_statfs] = ALLOW
        sec[sys_ftruncate64] = ALLOW
        sec[sys_clock_getres] = ALLOW
        sec[sys_socketcall] = ALLOW
        sec[sys_sched_yield] = ALLOW

        def tgkill(debugger):
            return debugger.arg0() == debugger.getpid()
        sec[sys_tgkill] = tgkill
        # Mono uses sys_kill to signal all other instances of it.

        def unlink(debugger):
            path = debugger.readstr(debugger.uarg0())
            if UNLINK_FS.match(path) is None:
                print 'Not allowed to unlink:', UNLINK_FS
                return False
            return True
        sec[sys_unlink] = unlink
        return sec

    def launch(self, *args, **kwargs):
        return SecurePopen([env['runtime']['mono'], self.name] + list(args),
                           security=self._get_security(),
                           address_grace=65536,
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={}, cwd=self._dir, nproc=-1)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen([env['runtime']['mono'], self.name] + list(args),
                                env={},
                                cwd=self._dir,
                                **kwargs)


def initialize():
    if 'csc' not in env['runtime'] or 'mono' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['csc']):
        return False
    return test_executor('CS', Executor, '''\
using System;

class test {
    public static void Main(string[] args) {
        Console.WriteLine("Hello, World!");
    }
}''')
