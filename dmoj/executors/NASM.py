from dmoj.executors.asm_executor import NASMExecutor, PlatformX86Mixin
from dmoj.judgeenv import env


class Executor(PlatformX86Mixin, NASMExecutor):
    as_path = env['runtime'].get('nasm', None)
    name = 'NASM'

    test_program = '''\
section .text
global  _start

_start:
        mov     eax,    4
        xor     ebx,    ebx
        inc     ebx
        mov     ecx,    msg
        mov     edx,    len
        int     80h

        xor     eax,    eax
        inc     eax
        int     80h

section .data

msg     db      'Hello, World!', 0xA
len     equ     $ - msg
'''


initialize = Executor.initialize
