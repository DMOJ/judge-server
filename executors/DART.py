from subprocess import Popen

from .resource_proxy import ResourceProxy
from .utils import test_executor
from cptbox import SecurePopen, CHROOTSecurity, PIPE
from judgeenv import env
from cptbox.syscalls import *

DART_FS = ['.*\.(so|dart)', '/proc/meminfo$', '/dev/urandom$']

class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.dart' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
    
    def _security(self):
        security = CHROOTSecurity(DART_FS)
        security[sys_epoll_create] = True
        security[sys_epoll_ctl] = True
        security[sys_timerfd_create] = True
        return security

    def launch(self, *args, **kwargs):
        return SecurePopen(['dart', self._script] + list(args),
                           executable=env['runtime']['dart'],
                           security=self._security(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072*2,
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['dart', self._script] + list(args),
                     executable=env['runtime']['dart'],
                     env={'LANG': 'C'},
                     cwd=self._dir,
                     **kwargs)


def initialize():
    if 'dart' not in env['runtime']:
        return False
    return test_executor('DART', Executor, '''\
void main() {
    print("Hello, World!");
}
''')

