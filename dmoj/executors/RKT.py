from dmoj.cptbox.handlers import ACCESS_DENIED
from dmoj.executors.base_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = '.rkt'
    name = 'RKT'
    fs = ['.*\.(?:so|rkt?$|zo$)', '/dev/tty$', '/proc/meminfo$', '.*racket.*', '/proc/stat$',
          '/proc/self/maps$', '/usr/lib', '/etc/nsswitch.conf$',
          '/etc/passwd$', '/dev/null$', '/sys/devices/system/cpu/online$']

    raco = env['runtime'].get('raco')
    command = env['runtime'].get('racket')

    syscalls = ['epoll_create', 'sigprocmask', 'rt_sigreturn', 'epoll_wait', 'poll',
                ('socketcall', ACCESS_DENIED), ('socket', ACCESS_DENIED),
                # PR_SET_NAME = 15
                ('prctl', lambda debugger: debugger.arg0 in (15,))]
    address_grace = 131072

    test_program = '''\
#lang racket
(displayln (read-line))
'''

    def get_compile_args(self):
        return [self.raco, 'make', self._code]

    def get_cmdline(self):
        return [self.get_command(), self._code]

    def get_executable(self):
        return self.get_command()

    @classmethod
    def initialize(cls, sandbox=True):
        if cls.raco is None:
            return False
        return super(Executor, cls).initialize(sandbox)
