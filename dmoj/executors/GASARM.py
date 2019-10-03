from dmoj.executors.asm_executor import GASExecutor
from dmoj.judgeenv import env
from dmoj.utils.os_ext import ARCH_ARM


class Executor(GASExecutor):
    arch = ARCH_ARM
    as_name = 'as_arm'
    ld_name = 'ld_arm'
    ld_m = 'armelf_linux_eabi'
    platform_prefixes = ['arm-linux-gnueabihf']

    qemu_path = env.runtime.qemu_arm
    dynamic_linker = env.runtime['ld.so_arm'] or '/lib/ld-linux-armhf.so.3'
    crt_pre = env.runtime.crt_pre_arm or ['/usr/lib/arm-linux-gnueabihf/crt1.o', '/usr/lib/arm-linux-gnueabihf/crti.o']
    crt_post = env.runtime.crt_post_arm or ['/usr/lib/arm-linux-gnueabihf/crtn.o']
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
