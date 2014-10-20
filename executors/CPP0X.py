from judgeenv import env
from .GCCExecutor import make_executor

Executor, initialize = make_executor('CPP0X', 'g++11', ['-std=c++0x'], '.cpp', r'''
#include <iostream>

int main() {
    auto message = "Hello, World!\n";
    std::cout << message;
    return 0;
}
''')

del make_executor, env
