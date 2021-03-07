#include <stdio.h>
#include <sys/ptrace.h>
#include <unistd.h>

int main() {
  if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1) {
    perror("ptrace");
  }
  return 0;
}
