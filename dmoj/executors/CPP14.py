from dmoj.executors.gcc_executor import CPPExecutor


class Executor(CPPExecutor):
    command = 'g++14'
    command_paths = ['g++-5', 'g++']
    std = 'c++14'
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
