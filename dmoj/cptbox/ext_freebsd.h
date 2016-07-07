#include <sys/ptrace.h>
#include <sys/types.h>

inline long ptrace_traceme() {
    return ptrace(PT_TRACE_ME, 0, NULL, 0);
}

// #include <bits/wordsize.h>
#define __WORDSIZE 64
#if __WORDSIZE == 64
struct linux_pt_reg
{
  unsigned long r15;
  unsigned long r14;
  unsigned long r13;
  unsigned long r12;
  unsigned long rbp;
  unsigned long rbx;
  unsigned long r11;
  unsigned long r10;
  unsigned long r9;
  unsigned long r8;
  unsigned long rax;
  unsigned long rcx;
  unsigned long rdx;
  unsigned long rsi;
  unsigned long rdi;
  unsigned long orig_rax;
  unsigned long rip;
  unsigned long cs;
  unsigned long eflags;
  unsigned long rsp;
  unsigned long ss;
  unsigned long fs_base;
  unsigned long gs_base;
  unsigned long ds;
  unsigned long es;
  unsigned long fs;
  unsigned long gs;
};

inline void map_regs_to_linux(struct reg *bsd_r, struct linux_pt_reg *linux_r)
{
	linux_r->rbp            = bsd_r->r_rbp;
	linux_r->rbx            = bsd_r->r_rbx;
	linux_r->r9             = bsd_r->r_r9;
	linux_r->r8             = bsd_r->r_r8;
	linux_r->rax            = bsd_r->r_rax;
	linux_r->rcx            = bsd_r->r_rcx;
	linux_r->rdx            = bsd_r->r_rdx;
	linux_r->rsi            = bsd_r->r_rsi;
	linux_r->rdi            = bsd_r->r_rdi;
	linux_r->orig_rax       = bsd_r->r_rax;
	linux_r->rsp            = bsd_r->r_rsp;

    /** the rest aren't copied **/
}

inline void map_regs_from_linux(struct reg *bsd_r, struct linux_pt_reg *linux_r)
{
    bsd_r->r_rbp    = linux_r->rbp;
    bsd_r->r_rbx    = linux_r->rbx;
    bsd_r->r_r9      = linux_r->r9;
    bsd_r->r_r8      = linux_r->r8;
    bsd_r->r_rax    = linux_r->rax;
    bsd_r->r_rcx    = linux_r->rcx;
    bsd_r->r_rdx    = linux_r->rdx;
    bsd_r->r_rsi    = linux_r->rsi;
    bsd_r->r_rdi    = linux_r->rdi;
    bsd_r->r_rsp    = linux_r->rsp;

    /** the rest aren't copied **/
}
#else /** WORDSIZE == 32 **/
struct linux_pt_reg
{
  long int ebx;
  long int ecx;
  long int edx;
  long int esi;
  long int edi;
  long int ebp;
  long int eax;
  long int xds;
  long int xes;
  long int xfs;
  long int xgs;
  long int orig_eax;
  long int eip;
  long int xcs;
  long int eflags;
  long int esp;
  long int xss;
};

inline void map_regs_to_linux(struct reg *bsd_r, struct linux_pt_reg *linux_r)
{
	linux_r->ebx = bsd_r->r_ebx;
	linux_r->ecx = bsd_r->r_ecx;
	linux_r->edx = bsd_r->r_edx;
	linux_r->esi = bsd_r->r_esi;
	linux_r->edi = bsd_r->r_edi;
	linux_r->ebp = bsd_r->r_ebp;
	linux_r->eax = bsd_r->r_eax;
	linux_r->orig_eax = bsd_r->r_eax;
	linux_r->esp = bsd_r->r_esp;

    /** the rest aren't copied **/
}

inline void map_regs_from_linux(struct reg *bsd_r, struct linux_pt_reg *linux_r)
{
	bsd_r->r_ebx = linux_r->ebx;
	bsd_r->r_ecx = linux_r->ecx;
	bsd_r->r_edx = linux_r->edx;
	bsd_r->r_esi = linux_r->esi;
	bsd_r->r_edi = linux_r->edi;
	bsd_r->r_ebp = linux_r->ebp;
	bsd_r->r_eax = linux_r->eax;
	bsd_r->r_esp = linux_r->esp;

    /** the rest aren't copied **/
}
#endif  /* __WORDSIZE */