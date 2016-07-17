from dmoj.executors.base_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = '.rkt'
    name = 'RKT'
    fs = ['/etc/nsswitch.conf$', '/etc/passwd$']

    command = 'racket'

    syscalls = ['epoll_create', 'epoll_wait', 'poll', 'select']
    address_grace = 131072

    test_program = '''\
#lang racket
(displayln (read-line))
'''

    def get_compile_args(self):
        return [self.runtime_dict['raco'], 'make', self._code]

    def get_cmdline(self):
        return [self.get_command(), self._code]

    def get_executable(self):
        return self.get_command()

    @classmethod
    def initialize(cls, sandbox=True):
        if 'raco' not in cls.runtime_dict:
            return False
        return super(Executor, cls).initialize(sandbox)

    @classmethod
    def get_find_first_mapping(cls):
        return {
            'racket': ['racket'],
            'raco': ['raco']
        }
