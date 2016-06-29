from dmoj.cptbox.handlers import ACCESS_DENIED
from dmoj.executors.base_executor import ScriptExecutor
from dmoj.judgeenv import env


class Executor(ScriptExecutor):
    ext = '.rkt'
    name = 'RKT'
    fs = ['.*\.(?:so|rkt?$)', '/dev/tty$', '/proc/meminfo$', '.*racket.*', '/proc/stat$',
          '/proc/self/maps$', '/usr/lib/i386-linux-gnu', '/etc/nsswitch.conf$',
          '/etc/passwd$', '/dev/null$', '/sys/devices/system/cpu/online$']
    command = env['runtime'].get('racket')
    syscalls = ['epoll_create', 'sigprocmask',
                ('socketcall', ACCESS_DENIED),
                ('prctl', lambda debugger: debugger.arg0 in (15,))]
    address_grace = 131072

    test_program = '''\
#lang racket
(displayln "Hello, World!")
'''

    def get_cmdline(self):
        return ['racket', self._code]


initialize = Executor.initialize
