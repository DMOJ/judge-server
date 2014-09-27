import os
from cptbox import SecurePopen, CHROOTSecurity
from executors.utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

PERL_FS = ['.*\.[so|pm]']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        source_code_file = str(problem_id) + '.pl'
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        self._files = [source_code_file]

    def launch(self, *args, **kwargs):
        return SecurePopen(['perl', self._files[0]] + list(args),
                           executable=env['runtime']['perl'],
                           security=CHROOTSecurity(PERL_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=16384)


def initialize():
    if 'perl' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['perl']):
        return False
    return test_executor('PERL', Executor, r'print "Hello, World!\n"')
