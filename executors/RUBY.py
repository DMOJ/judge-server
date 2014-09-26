import os
from cptbox import SecurePopen, CHROOTSecurity
from executors.utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

RUBY_FS = ['.*\.[so|rb]', '/dev/urandom']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        source_code_file = str(problem_id) + '.rb'
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        self._files = [source_code_file]

    def launch(self, *args, **kwargs):
        return SecurePopen(['ruby', self._files[0]] + list(args),
                           executable=env['runtime']['ruby'],
                           security=CHROOTSecurity(RUBY_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=65536)


def initialize():
    if 'ruby' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['ruby']):
        return False
    return test_executor('RUBY', Executor, "puts 'Hello, World!'")

