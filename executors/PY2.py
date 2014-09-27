from .resource_proxy import ResourceProxy
from .utils import test_executor
from cptbox import SecurePopen, CHROOTSecurity
from judgeenv import env

PYTHON_FS = ['.*\.[so|py]', '.*/lib(?:32|64)?/python[\d.]+/.*', '.*/lib/locale/.*', '/proc/meminfo']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        source_code_file = str(problem_id) + '.py'
        customize = '''\
# encoding: utf-8
__import__('sys').stdout = __import__('os').fdopen(1, 'w', 65536)
__import__('sys').stdin = __import__('os').fdopen(0, 'r', 65536)
'''
        with open(source_code_file, 'wb') as fo:
            fo.write(customize)
            fo.write(source_code)
        self._files = [source_code_file]

    def launch(self, *args, **kwargs):
        return SecurePopen(['python', '-BS', self._files[0]] + list(args),
                           executable=env['runtime']['python'],
                           security=CHROOTSecurity(PYTHON_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072,
                           env={'LANG': 'C'})


def initialize():
    if not 'python' in env['runtime']:
        return False
    return test_executor('PY2', Executor, 'print "Hello, World!"')
