section .text
global _start

_start:
    mov eax, 64
    int 80h

    mov ebx, eax
    mov ecx, 24
    mov eax, 37
    int 80h

    mov ebx, eax
    xor eax, eax
    inc eax
    int 80h
