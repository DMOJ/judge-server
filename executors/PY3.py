import os
from cptbox import CHROOTSecurity, SecurePopen
from executors.utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

PYTHON_FS = ['/dev/urandom$', '.*\.(?:so|py[co]?)$', '.*/lib(?:32|64)?/python[\d.]+/.*',
             '.*/lib/locale/', '/usr/lib64', '.*/?pyvenv.cfg$', '/proc/meminfo$',
             '/etc/ld\.so']
if 'python3dir' in env:
    PYTHON_FS += [str(env['python3dir']) + '.*']


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
                           executable=env['runtime']['python3'],
                           security=CHROOTSecurity(PYTHON_FS + [self._dir + '$']),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072,
                           env={'LANG': 'C'}, cwd=self._dir)


def initialize():
    if not 'python3' in env['runtime']:
        return False
    return test_executor('PY3', Executor, 'print("Hello, World!")')
