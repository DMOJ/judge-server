import os

from .base_executor import ScriptExecutor
from dmoj.judgeenv import env


class Executor(ScriptExecutor):
    ext = '.coffee'
    name = 'COFFEE'
    nproc = -1
    fs = ['.*\.(?:so|js$)', '/etc/(?:resolv|nsswitch).conf$', '/dev/urandom$',
          '/$', '/proc/meminfo$']
    command = env['runtime'].get('node')
    syscalls = ['timer_create', 'timer_settime', 'timer_delete', 'newselect', 'select', 'pipe2',
                'write', 'epoll_create1', 'eventfd2', 'epoll_ctl', 'epoll_wait']
    test_program = '''\
process.stdin.on 'readable', () ->
  chunk = process.stdin.read()
  if chunk != null
    process.stdout.write chunk
'''
    address_grace = 262144

    @classmethod
    def initialize(cls, sandbox=True):
        if 'coffee' not in env['runtime'] or not os.path.isfile(env['runtime']['coffee']):
            return False
        return super(Executor, cls).initialize(sandbox=sandbox)

    def get_cmdline(self):
        return [self.get_command(), env['runtime']['coffee'], self._code]

    def get_fs(self):
        return super(Executor, self).get_fs() + [env['runtime']['coffee']]
