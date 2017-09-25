import os
import re

from dmoj.error import CompileError
from .base_executor import CompiledExecutor

recomment = re.compile(r'//.*?(?=[\r\n])')
decomment = lambda x: recomment.sub('', x)

class Executor(CompiledExecutor):
    ext = '.go'
    name = 'GO'
    address_grace = 786432
    syscalls = ['modify_ldt', 'select', 'restart_syscall']
    command = 'go'
    test_name = 'echo'
    test_program = '''\
package main

import "os"
import "fmt"
import "bufio"

func main() {
    bio := bufio.NewReader(os.Stdin)
    text, _ := bio.ReadString(0)
    fmt.Print(text)
}'''

    def get_compile_args(self):
        return [self.get_command(), 'build', self._code]

    @classmethod
    def get_version_flags(cls, command):
        return ['version']

    def get_nproc(self):
        return [-1, 1][os.name == 'nt']

    def create_files(self, problem_id, source_code, *args, **kwargs):
        super(Executor, self).create_files(problem_id, source_code, *args, **kwargs)
        source_code = decomment(source_code).strip()
        if source_code.split('\n')[0].strip() != 'package main':
            raise CompileError('Your code must be defined in package main.\n')
