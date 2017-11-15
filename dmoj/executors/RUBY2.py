import os

from .ruby_executor import RubyExecutor


class Executor(RubyExecutor):
    name = 'RUBY2'
    command_paths = (['ruby2.%d' % i for i in reversed(xrange(0, 5))] +
                     ['ruby2%d' % i for i in reversed(xrange(0, 5))])
    syscalls = ['pipe2', 'poll', ('write', lambda debugger: debugger.arg0 in (1, 2, 4)), 'thr_set_name']
    fs = ['/proc/self/loginuid$', '/etc/nsswitch.conf$', '/etc/passwd$']

    def get_nproc(self):
        return [-1, 1][os.name == 'nt']
