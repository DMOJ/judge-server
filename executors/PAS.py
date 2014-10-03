import os
import subprocess
import sys

from cptbox import CHROOTSecurity, SecurePopen
from error import CompileError
from executors.utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

PAS_FS = ['.*\.so']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        source_code_file = self._file('%s.pas' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        self._executable = output_file = self._file(str(problem_id))
        fpc_args = [env['runtime']['fpc'], '-So', '-O2', source_code_file, '-o' + output_file]
        fpc_process = subprocess.Popen(fpc_args, stderr=subprocess.PIPE, cwd=self._dir)
        _, compile_error = fpc_process.communicate()
        if fpc_process.returncode != 0:
            raise CompileError(compile_error)
        self.name = problem_id

    def launch(self, *args, **kwargs):
        return SecurePopen([self.name] + list(args),
                           executable=self._executable,
                           security=CHROOTSecurity(PAS_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           env={}, cwd=self._dir)


def initialize():
    if 'fpc' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['fpc']):
        return False
    return test_executor('PAS', Executor, '''\
begin
    writeln('Hello, World!')
end.''')