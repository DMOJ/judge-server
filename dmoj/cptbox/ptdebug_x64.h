#pragma once
#ifndef ida57e8432_9ad6_4c63_8376_bb4395f2c3aa
#define ida57e8432_9ad6_4c63_8376_bb4395f2c3aa

#include <sys/user.h>

typedef union {
    struct user_regs_struct x64;
    struct {
        uint32_t ebx;
        uint32_t ecx;
        uint32_t edx;
        uint32_t esi;
        uint32_t edi;
        uint32_t ebp;
        uint32_t eax;
        uint32_t xds;
        uint32_t xes;
        uint32_t xfs;
        uint32_t xgs;
        uint32_t orig_eax;
        uint32_t eip;
        uint32_t xcs;
        uint32_t eflags;
        uint32_t esp;
        uint32_t xss;
    } x86;
} ptbox_regs;

#endif
