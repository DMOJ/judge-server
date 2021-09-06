from dmoj.executors.CPP03 import Executor as CPPExecutor


class Executor(CPPExecutor):
    command = 'g++11'
    command_paths = ['g++-5', 'g++-4.9', 'g++-4.8', 'g++']
    std = 'c++11'
    name = 'CPP11'
    test_program = """
#include <iostream>

int main() {
    auto input = std::cin.rdbuf();
    std::cout << input;
    return 0;
}
"""
