import subprocess

from dmoj.executors.script_executor import ScriptExecutor


class Executor(ScriptExecutor):
    ext = 'tcl'
    nproc = -1  # TCL uses a bunch of threads internally
    address_grace = 131072
    command = 'tclsh'
    syscalls = ['connect', 'access', 'getsockname']
    test_program = """\
gets stdin input
puts $input
"""

    @classmethod
    def get_runtime_versions(cls):
        # TCL is dangerous to fetch versions for, since some TCL versions ignore the --version flag and instead go
        # straight into the interpreter. Since version processes are ran without time limit, this is pretty bad since
        # it can hang the startup process. TCL versions without --version can't be reliably detected either, since
        # they also don't have --help.
        # Here, we just use subprocess to print the TCL version, and use that.
        process = subprocess.Popen([cls.get_command()], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        process.stdin.write(b'puts $tcl_version\n')
        process.stdin.close()
        retcode = process.poll()
        return (('tclsh', tuple(map(int, process.stdout.read().split(b'.'))) if not retcode else ()),)
