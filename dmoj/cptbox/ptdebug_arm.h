#pragma once
#ifndef id4e82dbcf_e693_404b_ba19_f27c2410e35c
#define id4e82dbcf_e693_404b_ba19_f27c2410e35c

#include <asm/ptrace.h>

// <asm/ptrace.h> defines this, which breaks it for ptrace use.
#ifdef PTRACE_SET_SYSCALL
#undef PTRACE_SET_SYSCALL
#endif

typedef struct pt_regs ptbox_regs;

#endif
