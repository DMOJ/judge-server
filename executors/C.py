from .GCCExecutor import GCCExecutor
from judgeenv import env


class Executor(GCCExecutor):
    command = env['runtime'].get('gcc')
    flags = ['-std=c99']
    ext = '.c'
    name = 'C'
    test_program = '''
#include <stdio.h>

int main() {
    int ch;
    while ((ch = getchar()) != EOF)
        putchar(ch);
    return 0;
}
'''

initialize = Executor.initialize
