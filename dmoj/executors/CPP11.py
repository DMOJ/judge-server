from dmoj.executors.CPP import Executor as CPPExecutor
from dmoj.judgeenv import env


class Executor(CPPExecutor):
    command = env['runtime'].get('g++11')
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

initialize = Executor.initialize
