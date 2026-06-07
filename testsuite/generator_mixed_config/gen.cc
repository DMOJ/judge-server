#include <cstdio>
#include <cstdlib>
int main(int argc, char **argv) {
  int T;
  if (argc == 1) {
    scanf("%d", &T);
    printf("%d\n", T+1);
    fprintf(stderr, "%d\n", T+1);
  } else {
    T = atoi(argv[1]);
    printf("%d\n", T+1);
    fprintf(stderr, "%d\n", T+1);
  }
}
