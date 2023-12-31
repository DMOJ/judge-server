from dmoj.executors.c_like_executor import CExecutor, CLANG_VERSIONS, ClangMixin


class Executor(ClangMixin, CExecutor):
    command = 'clang'
    std = 'c11'
    command_paths = [f'clang-{i}' for i in CLANG_VERSIONS] + ['clang']

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
