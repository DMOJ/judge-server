from .base_executor import CompiledExecutor
from judgeenv import env


class Executor(CompiledExecutor):
    ext = '.go'
    name = 'GO'
    address_grace = 131072
    fs = ['.*\.so', '/proc/stat$']
    syscalls = ['getpid', 'getppid', 'clock_getres', 'timer_create', 'timer_settime',
                'timer_delete', 'modify_ldt']
    command = env['runtime'].get('go')
    test_program = '''\
package main

import "fmt" "bufio"

func main() {
    bio := bufio.NewReader(os.Stdin)
    text, _ := bio.ReadString(0)
    fmt.Print(text)
}'''

    def get_compile_args(self):
        return [self.get_command(), 'build', self._code]


initialize = Executor.initialize