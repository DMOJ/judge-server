from dmoj.executors.c_like_executor import CPPExecutor, GCCMixin


class Executor(GCCMixin, CPPExecutor):
    command = 'g++23'
    command_paths = ['g++-13', 'g++']
    std = 'c++23'
    test_program = """
#include <iostream>

#if __cplusplus >= 202302L
int main() {
    auto input = std::cin.rdbuf();
    std::cout << input;
    return 0;
}
#endif
"""
