#include <stdio.h>
#include <sys/reboot.h>
#include <unistd.h>

int main() {
  if (reboot(RB_HALT) == -1) {
    perror("reboot");
  }
  return 0;
}
