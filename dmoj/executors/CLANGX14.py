from dmoj.executors.c_like_executor import CLANG_VERSIONS, CPPExecutor, ClangMixin


class Executor(ClangMixin, CPPExecutor):
    command = 'clang++'
    std = 'c++14'
    command_paths = [f'clang++-{i}' for i in CLANG_VERSIONS] + ['clang++']

    test_program = """
#include <iostream>

auto input() {
    return std::cin.rdbuf();
}

#if __cplusplus == 201402
int main() {
    std::cout << input();
    return 0;
}
#endif
"""
