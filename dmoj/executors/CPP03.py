from dmoj.executors.c_like_executor import CPPExecutor, GCCMixin


class Executor(GCCMixin, CPPExecutor):
    command = 'g++'
    std = 'c++03'
    test_program = """
#include <iostream>

#if __cplusplus >= 199711 && __cplusplus < 201103
int main() {
    std::cout << std::cin.rdbuf();
    return 0;
}
#endif
"""
