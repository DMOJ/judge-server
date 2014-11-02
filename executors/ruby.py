import os
from cptbox import SecurePopen, CHROOTSecurity
from .utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

RUBY_FS = ['.*\.(?:so|rb$)', '/dev/urandom$', '/proc/self']


def make_executor(key):
    class Executor(ResourceProxy):
        def __init__(self, problem_id, source_code):
            super(Executor, self).__init__()
            self._script = source_code_file = self._file('%s.rb' % problem_id)
            with open(source_code_file, 'wb') as fo:
                fo.write(source_code)

        def _nproc(self):
            return 0

        def _security(self):
            return CHROOTSecurity(RUBY_FS)

        def launch(self, *args, **kwargs):
            return SecurePopen(['ruby', self._script] + list(args),
                               executable=env['runtime'][key],
                               security=self._security(),
                               time=kwargs.get('time'),
                               memory=kwargs.get('memory'),
                               address_grace=65536, nproc=self._nproc(),
                               env={})
    return Executor


def make_initialize(name, key, Executor):
    def initialize():
        if key not in env['runtime']:
            return False
        if not os.path.isfile(env['runtime'][key]):
            return False
        return test_executor(name, Executor, "puts 'Hello, World!'")
    return initialize
