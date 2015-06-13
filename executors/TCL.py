from .resource_proxy import ResourceProxy
from .utils import test_executor
from cptbox import SecurePopen, CHROOTSecurity, PIPE
from judgeenv import env
from subprocess import Popen, PIPE as sPIPE
from cptbox.syscalls import *
import errno

TCL_FS = ['.*\.(so|tcl)', '/etc/nsswitch\.conf$', '/etc/passwd$']

class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        self._script = source_code_file = self._file('%s.tcl' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
    
    def _security(self):
        security = CHROOTSecurity(TCL_FS)
        def sock(debugger):
            def socket_return():
                debugger.result = -errno.EACCES
            debugger.syscall = debugger.getpid_syscall
            debugger.on_return(socket_return)
            return True
        def write(debugger):
            if debugger.arg0 > 4: # TCL uses some handles internally
                return False
            return True
        security[sys_tgkill] = True
        security[sys_write] = write
        security[sys_socket] = sock
        security[sys_connect] = True
        security[sys_access] = True
        security[sys_getsockname] = True
        return security

    def launch(self, *args, **kwargs):
        return SecurePopen(['tclsh', self._script] + list(args),
                           executable=env['runtime']['tclsh'],
                           security=self._security(),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           address_grace=131072,
                           stderr=(PIPE if kwargs.get('pipe_stderr', False) else None),
                           env={'LANG': 'C'}, cwd=self._dir)

    def launch_unsafe(self, *args, **kwargs):
        return Popen(['tclsh', self._script] + list(args),
                     executable=env['runtime']['tclsh'],
                     env={'LANG': 'C'},
                     cwd=self._dir,
                     **kwargs)


def initialize():
    if not 'tclsh' in env['runtime']:
        return False
    return test_executor('TCL', Executor, '''puts "Hello, World!"
''')

