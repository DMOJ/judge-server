#ifdef HAS_DEBUGGER_X32
#define _DEFAULT_SOURCE
#define _BSD_SOURCE

#include "ptbox.h"

#define ORIG_RAX 15

int pt_debugger_x32::syscall() {
    return (int) peek_reg(ORIG_RAX) & ~0x40000000;
}
#endif /* HAS_DEBUGGER_X32 */
