section .text
global _start

_start:
    mov rax, 110
    syscall

    mov rdi, rax
    mov rsi, 24
    mov rax, 62
    syscall

    mov rdi, rax
    mov rax, 231
    syscall

