from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'gcc11'
    flags = ['-std=c11']
    command_paths = ['gcc']
    ext = 'c'
    test_program = """
#include <stdio.h>

#if __STDC_VERSION__ == 201112
int main() {
    int ch;
    while ((ch = getchar()) != EOF)
        putchar(ch);
    return 0;
}
#endif
"""
