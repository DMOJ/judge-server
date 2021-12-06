from dmoj.executors.asm_executor import GASExecutor, PlatformX64Mixin


class Executor(PlatformX64Mixin, GASExecutor):
    as_name = 'as_x64'

    test_program = r""".intel_syntax noprefix

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
"""  # noqa: W191
