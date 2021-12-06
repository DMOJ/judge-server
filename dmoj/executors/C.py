from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'gcc'
    flags = ['-std=c99']
    ext = 'c'
    test_program = """
#include <stdio.h>

int main() {
    int ch;
    while ((ch = getchar()) != EOF)
        putchar(ch);
    return 0;
}
"""
