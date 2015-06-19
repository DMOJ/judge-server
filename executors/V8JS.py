import os
import subprocess
try:
    from cptbox import SecurePopen, CHROOTSecurity
except ImportError:
    from wbox import WBoxPopen
    SecurePopen = None

from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.js' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

    if SecurePopen is None:
        def launch(self, *args, **kwargs):
            return WBoxPopen(['v8dmoj', self._script] + list(args),
                             time=kwargs.get('time'), memory=kwargs.get('memory'),
                             cwd=self._dir, executable=env['runtime']['v8dmoj'],
                             network_block=True)
    else:
        def launch(self, *args, **kwargs):
            return SecurePopen([env['runtime']['v8dmoj'], self._script] + list(args),
                               security=CHROOTSecurity([]),
                               time=kwargs.get('time'),
                               memory=kwargs.get('memory'),
                               address_grace=786432,
                               env={}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen([env['runtime']['v8dmoj'], self._script] + list(args),
                                env={}, cwd=self._dir, **kwargs)


def initialize():
    if 'v8dmoj' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['v8dmoj']):
        return False
    return test_executor('JS', Executor, r"print('Hello, World!\n');")
