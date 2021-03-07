#include <stdio.h>
#include <stdlib.h>
FILE *proc_output;
void read(int *i) {
  if (fscanf(proc_output, "%d", i) != 1)
    exit(2);
}
int main(int argc, char *argv[]) {
  proc_output = fopen(argv[2], "r");
  int a, b;
  read(&a);
  read(&b);
  return a + b != 0;
}
