import os
from cptbox import SecurePopen, CHROOTSecurity
from executors.utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

RUBY_FS = ['.*\.(?:so|rb$)', '/dev/urandom$']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.rb' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

    def launch(self, *args, **kwargs):
        return SecurePopen(['ruby', self._script] + list(args),
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

