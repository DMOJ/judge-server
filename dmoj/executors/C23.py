from dmoj.executors.c_like_executor import CExecutor, GCCMixin


class Executor(GCCMixin, CExecutor):
    command = 'gcc23'
    std = 'c23'
    command_paths = ['gcc']

    test_program = """
#include <stdio.h>
#include <stddef.h>

#if __STDC_VERSION__ == 202311L
int main() {
    nullptr_t ptr = nullptr;
    int ch;
    while ((ch = getchar()) != EOF)
        putchar(ch);
    return 0;
}
#endif
"""
