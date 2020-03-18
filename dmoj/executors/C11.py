from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'gcc11'
    flags = ['-std=c11']
    command_paths = ['gcc']
    ext = 'c'
    name = 'C11'
    test_program = '''
#include <stdio.h>

int main() {
    int ch;
    while ((ch = getchar()) != EOF)
        putchar(ch);
    return 0;
}
'''
