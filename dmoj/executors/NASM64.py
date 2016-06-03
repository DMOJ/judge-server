from dmoj.executors.asm_executor import NASMExecutor, PlatformX64Mixin
from dmoj.judgeenv import env


class Executor(PlatformX64Mixin, NASMExecutor):
    as_path = env['runtime'].get('nasm', None)
    nasm_format = 'elf64'

    name = 'NASM64'

    test_program = '''\
section .text
global  _start

_start:
        xor     rax,    rax
        xor     rdi,    rdi
        mov     rsi,    buffer
        mov     rdx,    4096
        syscall

        test    rax,    rax
        jz      _exit

        mov     rdx,    rax
        xor     rax,    rax
        inc     rdi
        inc     rax
        syscall

        jmp     _start
_exit:
        mov     rax,    60
        xor     rdi,    rdi
        syscall

section .bss
    buffer  resb    4096
'''


initialize = Executor.initialize
