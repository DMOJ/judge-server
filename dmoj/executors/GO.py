import os

from .base_executor import CompiledExecutor


class Executor(CompiledExecutor):
    ext = '.go'
    name = 'GO'
    address_grace = 786432
    syscalls = ['modify_ldt', 'select']
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
