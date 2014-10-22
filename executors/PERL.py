import os
import subprocess
from cptbox import SecurePopen, CHROOTSecurity
from .utils import test_executor

from .resource_proxy import ResourceProxy
from judgeenv import env

PERL_FS = ['.*\.(?:so|p[lm]$)', '/dev/urandom']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.pl' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

    def launch(self, *args, **kwargs):
        return SecurePopen(['perl', self._script] + list(args),
                           executable=env['runtime']['perl'],
                           security=CHROOTSecurity(PERL_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=16384,
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return subprocess.Popen(['perl', self._script] + list(args),
                                executable=env['runtime']['perl'],
                                env={'LANG': 'C'},
                                cwd=self._dir,
                                **kwargs)


def initialize():
    if 'perl' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['perl']):
        return False
    return test_executor('PERL', Executor, r'print "Hello, World!\n"')
