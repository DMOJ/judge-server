import subprocess

from dmoj.executors.compiled_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = 'cbl'
    name = 'CBL'
    command = 'cobc'
    address_grace = 131072
    compile_output_index = 0
    test_program = '''\
	IDENTIFICATION DIVISION.
	PROGRAM-ID. HELLO-WORLD.
	PROCEDURE DIVISION.
		DISPLAY 'echo: Hello, World!'.
		STOP RUN.
'''  # noqa: W191

    def get_compile_args(self):
        return [self.get_command(), '-x', '-free', self._code]

    def get_compile_popen_kwargs(self):
        return {'stdout': subprocess.PIPE, 'stderr': subprocess.STDOUT}

    def get_compile_output(self, process):
        output = super().get_compile_output(process)
        return output if b'Error:' in output or b'Note:' in output or b'Warning:' in output else ''
