from .resource_proxy import ResourceProxy
from .utils import test_executor
from cptbox import SecurePopen, CHROOTSecurity, PIPE
from judgeenv import env
from subprocess import Popen

PYTHON_FS = ['.*\.(?:so|py[co]?$)', '/proc/cpuinfo$', '/proc/meminfo$']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.py' % problem_id)
        customize = '''\
# encoding: utf-8
__import__('sys').stdout = __import__('os').fdopen(1, 'w', 65536)
__import__('sys').stdin = __import__('os').fdopen(0, 'r', 65536)
'''
        with open(source_code_file, 'wb') as fo:
            fo.write(customize)
            fo.write(source_code)

    def _executable(self):
        return env['runtime']['pypy']

    def _get_security(self):
        return CHROOTSecurity(PYTHON_FS + ([env['runtime']['pypydir']] if 'pypydir' in env['runtime'] else []))

    def launch(self, *args, **kwargs):
        return SecurePopen([self._executable(), '-BS', self._script] + list(args),
                           executable=self._executable(),
                           security=self._get_security(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072,
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return Popen([self._executable(), '-BS', self._script] + list(args),
                     executable=self._executable(),
                     env={'LANG': 'C'},
                     cwd=self._dir,
                     **kwargs)


def initialize():
    if not 'pypy' in env['runtime']:
        return False
    return test_executor('PYPY', Executor, 'print "Hello, World!"')

