import errno

from executors.base_executor import ScriptExecutor
from judgeenv import env
from cptbox.syscalls import *


class Executor(ScriptExecutor):
    ext = '.tcl'
    name = 'TCL'
    address_grace = 131072
    command = env['runtime'].get('tclsh')
    fs = ['.*\.(so|tcl)', '/etc/nsswitch\.conf$', '/etc/passwd$']
    test_program = '''\
gets stdin input
puts $input
'''

    def get_security(self):
        security = super(Executor, self).get_security()

        def handle_socket(debugger):
            def socket_return():
                debugger.result = -errno.EACCES
            debugger.syscall = debugger.getpid_syscall
            debugger.on_return(socket_return)
            return True

        def handle_write(debugger):
            return debugger.arg0 <= 4 # TCL uses some handles internally
        security[sys_tgkill] = True
        security[sys_write] = handle_write
        security[sys_socket] = handle_socket
        security[sys_socketcall] = handle_socket
        security[sys_connect] = True
        security[sys_access] = True
        security[sys_getsockname] = True

        return security


initialize = Executor.initialize
