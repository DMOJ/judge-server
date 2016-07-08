from dmoj.executors.base_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = '.tcl'
    name = 'TCL'
    nproc = -1  # TCL uses a bunch of threads internally
    address_grace = 131072
    command = 'tclsh'
    syscalls = ['connect', 'access', 'getsockname', 'select',
                # TCL uses some handles internally
                ('write', lambda debugger: debugger.arg0 <= 7)]
    fs = ['.*\.tcl', '/etc/nsswitch\.conf$', '/etc/passwd$']
    test_program = '''\
gets stdin input
puts $input
'''
