import os
import subprocess

from cptbox import CHROOTSecurity, SecurePopen
from error import CompileError
from .utils import test_executor
from .resource_proxy import ResourceProxy
from judgeenv import env

ASM_FS = ['.*\.so']


class Executor(ResourceProxy):
    def __init__(self, problem_id, source_code):
        super(Executor, self).__init__()
        source_code_file = self._file('%s.asm' % problem_id)
        with open(source_code_file, 'wb') as fo:
            fo.write(source_code)
        obj_file = self._file('%s.o' % problem_id)
        self._executable = output_file = self._file(str(problem_id))
        nasm_process = subprocess.Popen([env['runtime']['nasm'], '-f', 'elf', source_code_file, '-o', obj_file],
                                        stderr=subprocess.PIPE, cwd=self._dir)
        _, compile_error = nasm_process.communicate()
        if nasm_process.returncode != 0:
            raise CompileError(compile_error)

        if 'gcc' in env['runtime'] and source_code.startswith('; libc'):
            ld_process = subprocess.Popen([env['runtime']['gcc'], obj_file, '-o', output_file],
                                          stderr=subprocess.PIPE, cwd=self._dir)
        else:
            ld_process = subprocess.Popen([env['runtime']['ld'], '-s', obj_file, '-o', output_file],
                                          stderr=subprocess.PIPE, cwd=self._dir)
        _, compile_error = ld_process.communicate()
        if ld_process.returncode != 0:
            raise CompileError(compile_error)
        self.name = problem_id

    def launch(self, *args, **kwargs):
        return SecurePopen([self.name] + list(args),
                           executable=self._executable,
                           security=CHROOTSecurity(ASM_FS),
                           time=kwargs.get('time'),
                           memory=kwargs.get('memory'),
                           env={}, cwd=self._dir)


def initialize():
    if 'nasm' not in env['runtime'] or 'ld' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['nasm']) or not os.path.isfile(env['runtime']['ld']):
        return False
    return test_executor('NASM', Executor, '''\
section .text
global  _start

_start:
        mov     eax,    4
        xor     ebx,    ebx
        inc     ebx
        mov     ecx,    msg
        mov     edx,    len
        int     80h

        xor     eax,    eax
        inc     eax
        int     80h

section .data

msg     db      'Hello, World!', 0xA
len     equ     $ - msg
''')