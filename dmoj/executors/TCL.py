import errno

from dmoj.cptbox.syscalls import *
from dmoj.executors.base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.tcl'
    name = 'TCL'
    address_grace = 131072
    command = 'tclsh'
    fs = ['.*\.tcl', '/etc/nsswitch\.conf$', '/etc/passwd$']
    test_program = '''\
gets stdin input
puts $input
'''

    def get_security(self, **kwargs):
        security = super(Executor, self).get_security(**kwargs)

        def handle_socket(debugger):
            def socket_return():
                debugger.result = -errno.EACCES

            debugger.syscall = debugger.getpid_syscall
            debugger.on_return(socket_return)
            return True

        security[sys_tgkill] = True
        security[sys_write] = lambda debugger: debugger.arg0 <= 4  # TCL uses some handles internally
        security[sys_socket] = handle_socket
        security[sys_socketcall] = handle_socket
        security[sys_connect] = True
        security[sys_access] = True
        security[sys_getsockname] = True

        return security
