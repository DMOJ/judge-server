from .gas_executor import GASExecutor
from judgeenv import env


class Executor(GASExecutor):
    as_path = env['runtime'].get('as_arm', None)
    ld_path = env['runtime'].get('ld_arm', None)
    qemu_path = env['runtime'].get('qemu_arm', None)
    name = 'GASARM'
    test_program = r'''
.global _start
_start:
  mov r7, #4
  mov r0, #1
  mov r2, #20
  ldr r1, =string
  swi 0
  mov r7, #1
  swi 0
.data
string:
  .ascii "echo: Hello, World!\n"
'''

initialize = Executor.initialize

