#include <sys/ptrace.h>
#include <sys/types.h>

inline long ptrace_traceme() {
    return ptrace(PT_TRACE_ME, 0, NULL, 0);
}

// Debian GNU/kFreeBSD neglected to define this in their libc.
#if defined(__FreeBSD_kernel__) && !defined(PT_FOLLOW_FORK)
#   define PT_FOLLOW_FORK 23
#endif

// Constant for wait4
#define __WALL 0

#if INTPTR_MAX == INT64_MAX
typedef unsigned long reg_type;

struct linux_pt_reg
{
  reg_type r15;
  reg_type r14;
  reg_type r13;
  reg_type r12;
  reg_type rbp;
  reg_type rbx;
  reg_type r11;
  reg_type r10;
  reg_type r9;
  reg_type r8;
  reg_type rax;
  reg_type rcx;
  reg_type rdx;
  reg_type rsi;
  reg_type rdi;
  reg_type orig_rax;
  reg_type rip;
  reg_type cs;
  reg_type eflags;
  reg_type rsp;
  reg_type ss;
  reg_type fs_base;
  reg_type gs_base;
  reg_type ds;
  reg_type es;
  reg_type fs;
  reg_type gs;
};

inline void map_regs_to_linux(struct reg *bsd_r, struct linux_pt_reg *linux_r)
{
	linux_r->rbp      = bsd_r->r_rbp;
	linux_r->rbx      = bsd_r->r_rbx;
	linux_r->r9       = bsd_r->r_r9;
	linux_r->r8       = bsd_r->r_r8;
	linux_r->rax      = bsd_r->r_rax;
	linux_r->rcx      = bsd_r->r_rcx;
	linux_r->rdx      = bsd_r->r_rdx;
	linux_r->rsi      = bsd_r->r_rsi;
	linux_r->rdi      = bsd_r->r_rdi;
	linux_r->orig_rax = bsd_r->r_rax;
	linux_r->rsp      = bsd_r->r_rsp;

    /** the rest aren't copied **/
}

inline void map_regs_from_linux(struct reg *bsd_r, struct linux_pt_reg *linux_r)
{
    bsd_r->r_rbp = linux_r->rbp;
    bsd_r->r_rbx = linux_r->rbx;
    bsd_r->r_r9  = linux_r->r9;
    bsd_r->r_r8  = linux_r->r8;
    bsd_r->r_rax = linux_r->rax;
    bsd_r->r_rcx = linux_r->rcx;
    bsd_r->r_rdx = linux_r->rdx;
    bsd_r->r_rsi = linux_r->rsi;
    bsd_r->r_rdi = linux_r->rdi;
    bsd_r->r_rsp = linux_r->rsp;

    /** the rest aren't copied **/
}
#elif INTPTR_MAX == INT32_MAX
typedef long int reg_type;

struct linux_pt_reg
{
  reg_type ebx;
  reg_type ecx;
  reg_type edx;
  reg_type esi;
  reg_type edi;
  reg_type ebp;
  reg_type eax;
  reg_type xds;
  reg_type xes;
  reg_type xfs;
  reg_type xgs;
  reg_type orig_eax;
  reg_type eip;
  reg_type xcs;
  reg_type eflags;
  reg_type esp;
  reg_type xss;
};

inline void map_regs_to_linux(struct reg *bsd_r, struct linux_pt_reg *linux_r)
{
	linux_r->ebx      = bsd_r->r_ebx;
	linux_r->ecx      = bsd_r->r_ecx;
	linux_r->edx      = bsd_r->r_edx;
	linux_r->esi      = bsd_r->r_esi;
	linux_r->edi      = bsd_r->r_edi;
	linux_r->ebp      = bsd_r->r_ebp;
	linux_r->eax      = bsd_r->r_eax;
	linux_r->orig_eax = bsd_r->r_eax;
	linux_r->esp      = bsd_r->r_esp;

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
#else
#error Missing size macros?
#endif
