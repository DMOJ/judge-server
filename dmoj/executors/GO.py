import os

from .base_executor import CompiledExecutor
from dmoj.judgeenv import env


class Executor(CompiledExecutor):
    ext = '.go'
    name = 'GO'
    address_grace = 786432
    fs = ['.*\.so', '/proc/stat$']
    syscalls = ['getpid', 'getppid', 'clock_getres', 'timer_create', 'timer_settime',
                'timer_delete', 'modify_ldt', 'sched_getaffinity']
    command = env['runtime'].get('go')
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

    def get_nproc(self):
        return [-1, 1][os.name == 'nt']


initialize = Executor.initialize
