from dmoj.executors.CPP import Executor as CPPExecutor


class Executor(CPPExecutor):
    command = 'g++11'
    std = 'c++11'
    name = 'CPP11'
    test_program = '''
#include <iostream>

int main() {
    auto input = std::cin.rdbuf();
    std::cout << input;
    return 0;
}
'''
