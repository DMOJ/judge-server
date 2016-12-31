#ifdef SIGNATURE_GRADER
#include <cstdio>

using namespace std;

int main()
{
    freopen("DATA.out", "w", stdout);
    freopen("DATA.in", "r", stdin);

    int N;
    scanf("%d", &N);

    while(N--) {
        int a, b;
        scanf("%d %d", &a, &b);
        printf("%d\n", a + b);
    }
    return 0;
}
#endif
