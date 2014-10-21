import os
import subprocess
from cptbox import SecurePopen, CHROOTSecurity, ALLOW
from cptbox.syscalls import *

from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

NODE_FS = ['.*\.so']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.js' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

    def _get_security(self):
        security = CHROOTSecurity(NODE_FS)
        security[sys_pipe2] = ALLOW
        return security

    def launch(self, *args, **kwargs):
        return SecurePopen([env['runtime']['node'], self._script] + list(args),
                           security=self._get_security(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=16384,
                           env={}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen([env['runtime']['node'], self._script] + list(args),
                                env={}, cwd=self._dir, **kwargs)


def initialize():
    if 'node' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['node']):
        return False
    return test_executor('JS', Executor, r"process.stdout.write('Hello, World!\n');")
