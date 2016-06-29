import errno

from dmoj.cptbox.syscalls import *
from dmoj.executors.base_executor import ScriptExecutor
from dmoj.judgeenv import env


class Executor(ScriptExecutor):
    ext = '.rkt'
    name = 'RKT'
    fs = ['.*\.(?:so|rkt?$)', '/dev/tty$', '/proc/meminfo$', '.*racket.*', '/proc/stat$',
          '/proc/self/maps$', '/usr/lib/i386-linux-gnu', '/etc/nsswitch.conf$',
          '/etc/passwd$', '/dev/null$', '/sys/devices/system/cpu/online$']
    command = env['runtime'].get('racket')
    syscalls = ['timer_create', 'timer_settime',
                'timer_delete', 'newselect', 'select']
    address_grace = 131072

    test_program = '''\
#lang racket
(displayln "Hello, World!")
'''

    def get_security(self):
        security = super(Executor, self).get_security()

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

    def get_cmdline(self):
        return ['racket', self._code]


initialize = Executor.initialize
