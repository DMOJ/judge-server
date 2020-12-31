#include <cstdio>
#include <cstdlib>
#include <unistd.h>
#include <sys/ptrace.h>

int main() {
    if (ptrace(PTRACE_TRACEME, 0, NULL, NULL) == -1) {
        perror("ptrace");
    }
    return 0;
}
