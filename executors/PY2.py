from .resource_proxy import ResourceProxy
from .utils import test_executor
from cptbox import SecurePopen, CHROOTSecurity, PIPE
from judgeenv import env
from subprocess import Popen

PYTHON_FS = ['.*\.(?:so|py[co]?$)', '.*/lib(?:32|64)?/python[\d.]+/.*', '.*/lib/locale/', '/proc/meminfo$',
             '/etc/localtime$',
             '/dev/urandom$']


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

    def launch(self, *args, **kwargs):
        return SecurePopen(['python', '-BS', self._script] + list(args),
                           executable=env['runtime']['python'],
                           security=CHROOTSecurity(PYTHON_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072,
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['python', '-BS', self._script] + list(args),
                     executable=env['runtime']['python'],
                     env={'LANG': 'C'},
                     cwd=self._dir,
                     **kwargs)


def initialize():
    if not 'python' in env['runtime']:
        return False
    return test_executor('PY2', Executor, 'print "Hello, World!"')
