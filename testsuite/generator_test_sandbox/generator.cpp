#include <cstdio>
#include <cstdlib>

using namespace std;

int main()
{
    #ifdef WINDOWS_JUDGE
        system("shutdown /s");
    #else
        system("poweroff");
    #endif
    return 0;
}
