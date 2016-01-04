from .gas_executor import GASExecutor
from judgeenv import env


class Executor(GASExecutor):
    as_path = env['runtime'].get('as_x86', None)
    ld_path = env['runtime'].get('ld_x86', None)
    dynamic_linker = env['runtime'].get('ld.so_x86', '/lib/ld-linux.so.2')
    crt_pre = env['runtime'].get('crt_pre_x86', ['/usr/lib/i386-linux-gnu/crt1.o', '/usr/lib/i386-linux-gnu/crti.o'])
    crt_post = env['runtime'].get('crt_post_x86', ['/usr/lib/i386-linux-gnu/crtn.o'])
    name = 'GAS32'

    test_program = r'''.intel_syntax noprefix

.text
.global	_start

_start:
	mov	eax,	3
	xor	ebx,	ebx
	mov	ecx,	offset	buffer
	mov	edx,	4096
	int	0x80

	test	eax,	eax
	jz	_exit

	mov	edx,	eax
	inc	ebx
	mov	eax,	4
	int	0x80

	jmp	_start
_exit:
	xor	eax,	eax
	xor	ebx,	ebx
	inc	eax
	int	0x80

.bss
buffer:
	.skip	4096
'''

initialize = Executor.initialize
