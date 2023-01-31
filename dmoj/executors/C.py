from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'gcc'
    flags = ['-std=c99']
    ext = 'c'
    test_program = """
#include <stdio.h>

#if __STDC_VERSION__ == 199901
int main() {
    int ch;
    while ((ch = getchar()) != EOF)
        putchar(ch);
    return 0;
}
#endif
"""
