from dmoj.executors.CPP import Executor as CPPExecutor


class Executor(CPPExecutor):
    command = 'g++14'
    std = 'c++14'
    name = 'CPP14'
    test_program = '''
#include <iostream>

auto input() {
    return std::cin.rdbuf();
}

int main() {
    std::cout << input();
    return 0;
}
'''
