from subprocess import Popen
import errno

from .resource_proxy import ResourceProxy
from .utils import test_executor
from cptbox import SecurePopen, CHROOTSecurity, PIPE
from cptbox.syscalls import *
from judgeenv import env

RACKET_FS = ['.*\.(?:so|rkt?$)', '/dev/tty$', '/proc/meminfo$', '.*racket.*', '/proc/stat$',
             '/proc/self/maps$', '/usr/lib/i386-linux-gnu', '/etc/nsswitch.conf$',
             '/etc/passwd$', '/dev/null$']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.rkt' % problem_id)

        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

    def _security(self):
        security = CHROOTSecurity(RACKET_FS)

        def handle_socketcall(debugger):
            def socket_return():
                debugger.result = -errno.EACCES

            debugger.syscall = debugger.getpid_syscall
            debugger.on_return(socket_return)
            return True

        security[sys_socketcall] = handle_socketcall
        security[sys_epoll_create] = True
        security[sys_sigprocmask] = True
        security[sys_prctl] = lambda debugger: debugger.arg0 in (15,)
        return security

    def launch(self, *args, **kwargs):
        return SecurePopen([env['runtime']['racket'], self._script] + list(args),
                           security=self._security(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072,
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return Popen([env['runtime']['racket'], self._script] + list(args),
                     env={'LANG': 'C'},
                     cwd=self._dir,
                     **kwargs)


def initialize(sandbox=True):
    if 'racket' not in env['runtime']:
        return False
    return test_executor('RKT', Executor, '''\
#lang racket
(displayln "Hello, World!")
''')
