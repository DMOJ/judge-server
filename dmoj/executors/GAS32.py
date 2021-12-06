from dmoj.executors.asm_executor import GASExecutor, PlatformX86Mixin


class Executor(PlatformX86Mixin, GASExecutor):
    as_name = 'as_x86'

    test_program = r""".intel_syntax noprefix

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
"""  # noqa: W191
