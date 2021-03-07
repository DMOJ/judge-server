#include <cstdio>

using namespace std;

int main() {
  freopen("in_link", "r", stdin);

  int N;
  scanf("%d", &N);

  while (N--) {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\n", a + b);
  }
  return 0;
}
