from dmoj.executors.c_like_executor import CExecutor, GCCMixin


class Executor(GCCMixin, CExecutor):
    command = 'gcc11'
    std = 'c11'
    command_paths = ['gcc']

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
