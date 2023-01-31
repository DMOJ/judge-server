from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'g++'
    std: str = 'c++03'
    ext = 'cpp'
    test_program = """
#include <iostream>

int main() {
    std::cout << std::cin.rdbuf();
    return 0;
}
"""

    def get_flags(self):
        return ([f'-std={self.std}']) + super().get_flags()
