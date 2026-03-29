from dmoj.executors.c_like_executor import CLANG_VERSIONS, CPPExecutor, ClangMixin


class Executor(ClangMixin, CPPExecutor):
    command = 'clang++'
    std = 'c++23'
    command_paths = [f'clang++-{i}' for i in CLANG_VERSIONS] + ['clang++']

    test_program = """
#include <iostream>

#if __cplusplus == 202302L
int main() {
    auto input = std::cin.rdbuf();
    std::cout << input;
    return 0;
}
#endif
"""
