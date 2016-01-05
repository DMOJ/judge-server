from .gas_executor import GASExecutor
from judgeenv import env


class Executor(GASExecutor):
    as_path = env['runtime'].get('as_x64', None)
    ld_path = env['runtime'].get('ld_x64', None)
    qemu_path = env['runtime'].get('qemu_x64', None)
    dynamic_linker = env['runtime'].get('ld.so_x64', '/lib64/ld-linux-x86-64.so.2')
    crt_pre = env['runtime'].get('crt_pre_x64', ['/usr/lib/x86_64-linux-gnu/crt1.o', '/usr/lib/x86_64-linux-gnu/crti.o'])
    crt_post = env['runtime'].get('crt_post_x64', ['/usr/lib/x86_64-linux-gnu/crtn.o'])
    name = 'GAS64'

    test_program = r'''.intel_syntax noprefix

.text
.global  _start

_start:
	xor	rax,	rax
	xor	rdi,	rdi
	mov	rsi,	offset	buffer
	mov	rdx,	4096
	syscall

	test	rax,	rax
	jz	_exit

	mov	rdx,	rax
	xor	rax,	rax
	inc	rdi
	inc	rax
	syscall

	jmp	_start
_exit:
	mov	rax,	60
	xor	rdi,	rdi
	syscall

.bss
buffer:
	.skip	4096
'''

initialize = Executor.initialize
