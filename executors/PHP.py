import os
import subprocess
from cptbox import SecurePopen, CHROOTSecurity
from .utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

PHP_FS = ['.*\.so', '/etc/localtime$', '.*/php[\w-]*\.ini$']
if 'phpconfdir' in env['runtime']:
    PHP_FS += [env['runtime']['phpconfdir']]

class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.php' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

    def launch(self, *args, **kwargs):
        return SecurePopen(['php', self._script] + list(args),
                           executable=env['runtime']['php'],
                           security=CHROOTSecurity(PHP_FS + [self._script]),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=16384,
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen(['php', self._script] + list(args),
                                executable=env['runtime']['php'],
                                env={'LANG': 'C'},
                                cwd=self._dir,
                                **kwargs)


def initialize():
    if 'php' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['php']):
        return False
    return test_executor('PHP', Executor, r'<?php echo "Hello, World!\n";')
