import os
import subprocess
import sys

from cptbox import CHROOTSecurity, SecurePopen
from error import CompileError
from executors.utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

PAS_FS = ['.*\.[so]']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        source_code_file = str(problem_id) + '.pas'
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        output_file = str(problem_id)
        fpc_args = [env['runtime']['fpc'], '-So', '-O2', source_code_file, '-o' + output_file]
        fpc_process = subprocess.Popen(fpc_args, stderr=subprocess.PIPE)
        _, compile_error = fpc_process.communicate()
        if fpc_process.returncode != 0:
            os.unlink(source_code_file)
            raise CompileError(compile_error)
        self._files = [source_code_file, output_file]
        self.name = problem_id

    def launch(self, *args, **kwargs):
        return SecurePopen([self.name] + list(args),
                           executable=self._files[1],
                           security=CHROOTSecurity(PAS_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           env={})


def initialize():
    if 'fpc' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['fpc']):
        return False
    return test_executor('PAS', Executor, '''\
begin
    writeln('Hello, World!')
end.''')