import subprocess

from cptbox import CHROOTSecurity, SecurePopen
from error import CompileError
from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

CBL_FS = ['.*\.so']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        source_code_file = self._file('%s.cbl' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        self._executable = self._file(str(problem_id))
        cbl_args = [env['runtime']['cobc'], '-x', source_code_file]
        cbl_process = subprocess.Popen(cbl_args, stdout=subprocess.PIPE, cwd=self._dir)
        compile_error, _ = cbl_process.communicate()
        if cbl_process.returncode != 0:
            raise CompileError(compile_error)
        self.name = problem_id
        self.warning = compile_error if 'Warning:' in compile_error or 'Note:' in compile_error else None

    def launch(self, *args, **kwargs):
        return SecurePopen([self.name] + list(args),
                           executable=self._executable,
                           security=CHROOTSecurity(CBL_FS),
                           address_grace=131072,
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           env={}, cwd=self._dir)


def initialize():
    if 'cobc' not in env['runtime']:
        return False
    return test_executor('CBL', Executor, '''\
	IDENTIFICATION DIVISION.
	PROGRAM-ID. HELLO-WORLD.
	PROCEDURE DIVISION.
		DISPLAY 'Hello, World!'.
		STOP RUN.
''')
