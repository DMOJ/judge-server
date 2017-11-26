import os

from .base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.coffee'
    name = 'COFFEE'
    nproc = -1
    command = 'node'
    syscalls = ['newselect', 'select', 'pipe2', 'poll', 'write', 'epoll_create1',
                'eventfd2', 'epoll_ctl', 'epoll_wait', 'sched_yield', 'setrlimit']
    test_program = '''\
process.stdin.on 'readable', () ->
  chunk = process.stdin.read()
  if chunk != null
    process.stdout.write chunk
'''
    address_grace = 1048576

    @classmethod
    def initialize(cls, sandbox=True):
        if 'coffee' not in cls.runtime_dict or not os.path.isfile(cls.runtime_dict['coffee']):
            return False
        return super(Executor, cls).initialize(sandbox=sandbox)

    def get_cmdline(self):
        return [self.get_command(), self.runtime_dict['coffee'], self._code]

    def get_fs(self):
        return super(Executor, self).get_fs() + [self.runtime_dict['coffee'], self._code]

    @classmethod
    def get_versionable_commands(cls):
        return ('coffee', cls.runtime_dict['coffee']), ('node', cls.runtime_dict['node'])

    @classmethod
    def get_find_first_mapping(cls):
        return {
            'node': ['nodejs', 'node'],
            'coffee': ['coffee']
        }
