from dmoj.executors.asm_executor import NASMExecutor, PlatformX86Mixin


class Executor(PlatformX86Mixin, NASMExecutor):
    nasm_format = 'elf32'

    test_program = """\
section .text
global  _start

_start:
        mov     eax,    3
        xor     ebx,    ebx
        mov     ecx,    buffer
        mov     edx,    4096
        int     0x80

        test    eax,    eax
        jz      _exit

        mov     edx,    eax
        inc     ebx
        mov     eax,    4
        int     80h

        jmp     _start
_exit:
        xor     eax,    eax
        xor     ebx,    ebx
        inc     eax
        int     80h


section .bss
    buffer  resb    4096
"""
