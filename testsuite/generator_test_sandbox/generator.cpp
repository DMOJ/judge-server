#include <cstdio>
#include <cstdlib>
#include <sys/ptrace.h>
#include <unistd.h>

int main() {
#if defined(__FreeBSD__) || defined(__FreeBSD_kernel__)
  if (ptrace(PT_TRACE_ME, 0, NULL, 0) == -1)
#else
  if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1)
#endif
  {
    perror("ptrace");
  }
  return 0;
}
