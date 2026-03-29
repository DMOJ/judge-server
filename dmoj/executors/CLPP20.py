from dmoj.executors.c_like_executor import CLANG_VERSIONS, CPPExecutor, ClangMixin


class Executor(ClangMixin, CPPExecutor):
    command = 'clang++'
    std = 'c++20'
    command_paths = [f'clang++-{i}' for i in CLANG_VERSIONS] + ['clang++']

    test_program = """
#include <iostream>

#if __cplusplus == 202002
int main() {
    std::strong_ordering comparison = 1 <=> 2;
    auto input = std::cin.rdbuf();
    std::cout << input;
    return 0;
}
#endif
"""
