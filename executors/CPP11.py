import os
import subprocess
import sys

from cptbox import CHROOTSecurity, SecurePopen
from error import CompileError
from executors.utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

C_FS = ['.*\.[so]']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(ResourceProxy, self).__init__()
        source_code_file = str(problem_id) + '.cpp'
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        if sys.platform == 'win32':
            compiled_extension = '.exe'
            linker_options = ['-Wl,--stack,8388608', '-static']
        else:
            compiled_extension = ''
            linker_options = []
        output_file = str(problem_id) + compiled_extension
        gcc_args = [env['runtime']['g++11'], source_code_file, '-O2',
                    '-std=' + env['runtime'].get('g++11std', 'c++0x'), '-march=native'
                   ] + linker_options + ['-s', '-o', output_file]
        gcc_process = subprocess.Popen(gcc_args, stderr=subprocess.PIPE)
        _, compile_error = gcc_process.communicate()
        self._files = [source_code_file, output_file]
        self.name = problem_id
        if gcc_process.returncode != 0:
            os.unlink(source_code_file)
            raise CompileError(compile_error)

    def launch(self, *args, **kwargs):
        return SecurePopen([self.name] + list(args),
                           executable=self._files[1],
                           security=CHROOTSecurity(C_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'))


def initialize():
    if 'g++11' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['g++11']):
        return False
    return test_executor('CPP11', Executor, r'''\
#include <iostream>

int main() {
    auto message = "Hello, World!\n";
    std::cout << message;
    return 0;
}
''')
