#ifndef id6ef72cec_c4c7_4879_9591_5c984afaa8a5
#define id6ef72cec_c4c7_4879_9591_5c984afaa8a5

#include <asm/ptrace.h>

typedef union {
    struct user_pt_regs arm64;
    struct {
        uint32_t r0;
        uint32_t r1;
        uint32_t r2;
        uint32_t r3;
        uint32_t r4;
        uint32_t r5;
        uint32_t r6;
        uint32_t r7;
        uint32_t r8;
        uint32_t r9;
        uint32_t r10;
        uint32_t fp;
        uint32_t ip;
        uint32_t sp;
        uint32_t lr;
        uint32_t pc;
        uint32_t cpsr;
        uint32_t orig_r0;
    } arm32;
} ptbox_regs;

#endif
