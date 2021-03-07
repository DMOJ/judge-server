#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
  int T = atoi(argv[1]);
  if (T == 1) {
    fprintf(stdout, "Hi\r\n");
    fprintf(stderr, "Hi\r\n");
  } else if (T == 2) {
    fprintf(stdout, "Hi\r");
    fprintf(stderr, "Hi\r");
  } else if (T == 3) {
    fprintf(stdout, "Hi\n");
    fprintf(stderr, "Hi\n");
  }
  fflush(stdout);
  fflush(stderr);
}
