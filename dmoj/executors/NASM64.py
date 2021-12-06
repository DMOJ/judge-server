from dmoj.executors.asm_executor import NASMExecutor, PlatformX64Mixin


class Executor(PlatformX64Mixin, NASMExecutor):
    nasm_format = 'elf64'

    test_program = """\
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
"""
