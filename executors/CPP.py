from .GCCExecutor import make_executor

Executor, initialize = make_executor('CPP', 'g++', [], '.cpp', r'''
#include <iostream>

int main() {
    std::cout << "Hello, World!\n";
    return 0;
}
''')

del make_executor
