from dmoj.executors.CPP03 import Executor as CPPExecutor


class Executor(CPPExecutor):
    command = 'g++17'
    command_paths = ['g++-7', 'g++']
    std = 'c++17'
    name = 'CPP17'
    test_program = """
#include <iostream>

int main() {
    float literal = 0x3.ABCp-10;
    auto input = std::cin.rdbuf();
    std::cout << input;
    return 0;
}
"""
