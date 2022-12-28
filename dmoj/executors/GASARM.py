from dmoj.executors.asm_executor import GASExecutor, PlatformARMMixin


class Executor(PlatformARMMixin, GASExecutor):
    as_name = 'as_arm'
    test_program = r"""
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
"""
