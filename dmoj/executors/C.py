from dmoj.executors.c_like_executor import CExecutor, GCCMixin


class Executor(GCCMixin, CExecutor):
    command = 'gcc'
    std = 'c99'

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
