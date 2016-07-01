from dmoj.cptbox.sandbox import ARM
from dmoj.executors.asm_executor import GASExecutor
from dmoj.judgeenv import env


class Executor(GASExecutor):
    arch = ARM
    as_path = env['runtime'].get('as_arm', None)
    ld_path = env['runtime'].get('ld_arm', None)
    qemu_path = env['runtime'].get('qemu_arm', None)
    dynamic_linker = env['runtime'].get('ld.so_x86', '/lib/ld-linux-armhf.so.3')
    crt_pre = env['runtime'].get('crt_pre_x86',
                                 ['/usr/lib/arm-linux-gnueabihf/crt1.o', '/usr/lib/arm-linux-gnueabihf/crti.o'])
    crt_post = env['runtime'].get('crt_post_x86', ['/usr/lib/arm-linux-gnueabihf/crtn.o'])
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
