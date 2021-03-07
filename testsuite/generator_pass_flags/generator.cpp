#include <cstdio>
#include <cstdlib>

#ifdef FLAG
void gen(int N) {
  printf("%d\n", N);
  for (int i = 0; i < N; i++) {
    int a = rand() % 10, b = rand() % 10;
    printf("%d %d\n", a, b);
    fprintf(stderr, "%d\n", a + b);
  }
  fflush(stdout);
  fflush(stderr);
}

int main(int argc, char *argv[]) {
  int T = atoi(argv[1]);
  if (T == 1)
    gen(10);
  else if (T == 2)
    gen(1000);
  else if (T == 3)
    gen(1000000);
  else if (T == 4)
    gen(10000000);
  return 0;
}
#endif
