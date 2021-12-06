import subprocess

from dmoj.cptbox.filesystem_policies import ExactFile
from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'cbl'
    command = 'cobc'
    address_grace = 131072
    compile_output_index = 0
    compiler_read_fs = [
        ExactFile('/etc/gnucobol/default.conf'),
    ]
    test_program = """\
	IDENTIFICATION DIVISION.
	PROGRAM-ID. HELLO-WORLD.
	PROCEDURE DIVISION.
		DISPLAY 'echo: Hello, World!'.
		STOP RUN.
"""  # noqa: W191

    def get_compile_args(self):
        return [self.get_command(), '-x', '-free', self._code]

    def get_compile_popen_kwargs(self):
        return {'stdout': subprocess.PIPE, 'stderr': subprocess.STDOUT}

    def get_compile_output(self, process):
        output = super().get_compile_output(process)
        # Some versions of the compiler have the first letter capitalized, and
        # others don't.
        for prefix in (b'Error:', b'Note:', b'Warning:'):
            if prefix in output or prefix.lower() in output:
                return output
        return b''
