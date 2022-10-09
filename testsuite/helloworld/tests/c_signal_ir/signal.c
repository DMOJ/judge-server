#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>

void handle_alarm(int _) {
  printf("Hello, World!\n");
  exit(1);
}

int main(void) {
  signal(SIGVTALRM, handle_alarm);
  raise(SIGVTALRM);

  for (;;) { __asm__ volatile ("nop"); }
  return 0;
}
