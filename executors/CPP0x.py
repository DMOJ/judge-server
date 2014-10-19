from judgeenv import env
from .GCCExecutor import make_executor

Executor, initialize = make_executor('CPP11', 'g++11', ['-std=' + env['runtime'].get('g++11std', 'c++0x')], '.cpp', r'''
#include <iostream>

int main() {
    auto message = "Hello, World!\n";
    std::cout << message;
    return 0;
}
''', 'g++')

del make_executor, env
