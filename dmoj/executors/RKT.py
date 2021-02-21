import os

from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'rkt'
    name = 'RKT'
    fs = [os.path.expanduser(r'~/\.racket/'), os.path.expanduser(r'~/\.local/share/racket/'),
          '/etc/racket/.*?', '/etc/passwd$']

    command = 'racket'

    syscalls = ['epoll_create', 'epoll_wait']
    # Racket SIGABRTs under low-memory conditions before actually crossing the memory limit,
    # so give it a bit of headroom to be properly marked as MLE.
    data_grace = 4096
    address_grace = 131072

    test_program = '''\
#lang racket
(displayln (read-line))
'''

    def get_compile_args(self):
        return [self.runtime_dict['raco'], 'make', self._code]

    def get_cmdline(self, **kwargs):
        return [self.get_command(), self._code]

    def get_executable(self):
        return self.get_command()

    @classmethod
    def initialize(cls):
        if 'raco' not in cls.runtime_dict:
            return False
        return super().initialize()

    @classmethod
    def get_versionable_commands(cls):
        return [('racket', cls.get_command())]

    @classmethod
    def get_find_first_mapping(cls):
        return {'racket': ['racket'], 'raco': ['raco']}
