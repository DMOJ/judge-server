from dmoj.cptbox.handlers import ACCESS_DENIED
from dmoj.executors.base_executor import ScriptExecutor
from dmoj.judgeenv import env


class Executor(ScriptExecutor):
    ext = '.rkt'
    name = 'RKT'
    fs = ['.*\.(?:so|rkt?$)', '/dev/tty$', '/proc/meminfo$', '.*racket.*', '/proc/stat$',
          '/proc/self/maps$', '/usr/lib', '/etc/nsswitch.conf$',
          '/etc/passwd$', '/dev/null$', '/sys/devices/system/cpu/online$']
    command = env['runtime'].get('racket')
    syscalls = ['epoll_create', 'sigprocmask', 'rt_sigreturn', 'epoll_wait', 'poll',
                ('socketcall', ACCESS_DENIED), ('socket', ACCESS_DENIED),
                ('prctl', lambda debugger: debugger.arg0 in (15,))]
    address_grace = 131072

    test_program = '''\
#lang racket
(displayln (read-line))
'''

initialize = Executor.initialize
