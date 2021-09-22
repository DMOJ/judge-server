import subprocess

from dmoj.executors.base_executor import RuntimeVersionList
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
    def get_runtime_versions(cls) -> RuntimeVersionList:
        # TCL is dangerous to fetch versions for, since some TCL versions ignore the --version flag and instead go
        # straight into the interpreter. Since version processes are ran without time limit, this is pretty bad since
        # it can hang the startup process. TCL versions without --version can't be reliably detected either, since
        # they also don't have --help.
        # Here, we just use subprocess to print the TCL version, and use that.
        command = cls.get_command()
        assert command is not None
        process = subprocess.Popen([command], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        assert process.stdin is not None
        assert process.stdout is not None
        process.stdin.write(b'puts $tcl_version\n')
        process.stdin.close()
        retcode = process.wait()
        return [('tclsh', tuple(map(int, process.stdout.read().split(b'.'))) if not retcode else ())]
