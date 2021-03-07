#include <cstdio>

using namespace std;

int main() {
  int N;
  scanf("%d", &N);

  while (N--) {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\n", a + b);
  }
  return 0;
}