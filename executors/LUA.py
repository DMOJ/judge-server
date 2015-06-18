from .resource_proxy import ResourceProxy
from .utils import test_executor
from cptbox import SecurePopen, CHROOTSecurity, PIPE
from judgeenv import env
from subprocess import Popen, PIPE as sPIPE

LUA_FS = ['.*\.(so|lua)']

class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.lua' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)

    def launch(self, *args, **kwargs):
        return SecurePopen(['lua', self._script] + list(args),
                           executable=env['runtime']['lua'],
                           security=CHROOTSecurity(LUA_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072,
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['lua', self._script] + list(args),
                     executable=env['runtime']['lua'],
                     env={'LANG': 'C'},
                     cwd=self._dir,
                     **kwargs)


def initialize():
    if not 'lua' in env['runtime']:
        return False
    return test_executor('LUA', Executor, 'print "Hello, World!"')

