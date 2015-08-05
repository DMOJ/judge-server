from .CPP import Executor as CPPExecutor
from judgeenv import env


class Executor(CPPExecutor):
    command = env['runtime'].get('g++14')
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

initialize = Executor.initialize
