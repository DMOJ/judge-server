#include "header.h"
#include <stdbool.h>
#include <stdio.h>

int main() {
  int n;
  scanf("%d", &n);
  bool valid = is_valid(n); // Defined in header
  printf(valid ? "correct" : "wrong");
  return 0;
}