from dmoj.executors.CPP03 import Executor as CPPExecutor


class Executor(CPPExecutor):
    command = 'g++14'
    command_paths = ['g++-5', 'g++']
    std = 'c++14'
    test_program = """
#include <iostream>

auto input() {
    return std::cin.rdbuf();
}

int main() {
    std::cout << input();
    return 0;
}
"""
