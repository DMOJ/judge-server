from .gas_executor import GASExecutor
from judgeenv import env


class Executor(GASExecutor):
    as_path = env['runtime'].get('asx86', None)
    ld_path = env['runtime'].get('ldx86', None)
    name = 'GAS32'
    test_program = r'''.intel_syntax noprefix

.text
.global  _start

_start:
        mov     eax,    4
        xor     ebx,    ebx
        inc     ebx
        mov     ecx,    offset msg
        mov     edx,    offset len
        int     0x80

        xor     eax,    eax
        inc     eax
        int     0x80

.data
msg:
        .ascii  "echo: Hello, World!\n"
        len = . - msg
'''

initialize = Executor.initialize

