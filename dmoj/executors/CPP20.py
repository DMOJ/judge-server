from dmoj.executors.c_like_executor import CPPExecutor, GCCMixin


class Executor(GCCMixin, CPPExecutor):
    command = 'g++20'
    command_paths = ['g++-11', 'g++']
    std = 'c++20'
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
