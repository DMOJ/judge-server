from dmoj.executors.base_executor import ScriptExecutor
import os

if os.name != 'nt':
    from dmoj.cptbox.handlers import ACCESS_DENIED


def do_write(debugger):
    if debugger.arg0 <= 2:
        return True
    # TCL doesn't seem to care if anything past 2 fails
    return ACCESS_DENIED(debugger)


class Executor(ScriptExecutor):
    ext = '.tcl'
    name = 'TCL'
    nproc = -1  # TCL uses a bunch of threads internally
    address_grace = 131072
    command = 'tclsh'
    syscalls = ['connect', 'access', 'getsockname', 'select',
                # TCL uses some handles internally
                ('write', do_write)]
    fs = [r'/etc/nsswitch\.conf$', '/etc/passwd$']
    test_program = '''\
gets stdin input
puts $input
'''
