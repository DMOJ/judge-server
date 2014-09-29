import os
import subprocess
import sys

from cptbox import CHROOTSecurity, SecurePopen
from error import CompileError
from executors.utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

C_FS = ['.*\.[so]']


def make_executor(code, command, args, ext, test_code):
    class Executor(ResourceProxy):
        def __init__(self, problem_id, source_code):
            super(ResourceProxy, self).__init__()
            source_code_file = self._file('%s%s' % (problem_id, ext))
            with open(source_code_file, 'wb') as fo:
                fo.write(source_code)
            if sys.platform == 'win32':
                compiled_extension = '.exe'
                linker_options = ['-Wl,--stack,8388608', '-static']
            else:
                compiled_extension = ''
                linker_options = []
            output_file = self._file('%s%s' % (problem_id, compiled_extension))
            gcc_args = [command, source_code_file, '-O2', '-march=native'
                        ] + args + linker_options + ['-s', '-o', output_file]
            gcc_process = subprocess.Popen(gcc_args, stderr=subprocess.PIPE, executable=env['runtime'][command],
                                           cwd=self._dir)
            _, compile_error = gcc_process.communicate()
            if gcc_process.returncode != 0:
                raise CompileError(compile_error)
            self._executable = output_file
            self.name = problem_id

        def launch(self, *args, **kwargs):
            return SecurePopen([self.name] + list(args),
                               executable=self._executable,
                               security=CHROOTSecurity(C_FS),
                               time=kwargs.get('time'),
                               memory=kwargs.get('memory'),
                               env={}, cwd=self._dir)

    def initialize():
        if command not in env['runtime']:
            return False
        if not os.path.isfile(env['runtime'][command]):
            return False
        return test_executor(code, Executor, test_code)
    return Executor, initialize
