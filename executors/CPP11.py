from judgeenv import env
from .GCCExecutor import make_executor

Executor, initialize = make_executor('CPP11', 'g++11', ['-std=c++11'], '.cpp', r'''
#include <iostream>

int main() {
    auto message = "Hello, World!\n";
    std::cout << message;
    return 0;
}
''')

del make_executor, env
