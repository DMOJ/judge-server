import subprocess

from .base_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = '.cbl'
    name = 'CBL'
    command = 'cobc'
    address_grace = 131072
    test_program = '''\
	IDENTIFICATION DIVISION.
	PROGRAM-ID. HELLO-WORLD.
	PROCEDURE DIVISION.
		DISPLAY 'echo: Hello, World!'.
		STOP RUN.
'''

    def get_compile_args(self):
        return [self.get_command(), '-x', self._code]

    def get_compile_popen_kwargs(self):
        return {'stdout': subprocess.PIPE, 'stderr': None}

    def get_compile_output(self, process):
        output = process.communicate()[0]
        return output if b'Error:' in output or b'Note:' in output or b'Warning:' in output else None
