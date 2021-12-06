from typing import Optional

from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'g++'
    std: Optional[str] = None
    ext = 'cpp'
    test_program = """
#include <iostream>

int main() {
    std::cout << std::cin.rdbuf();
    return 0;
}
"""

    def get_flags(self):
        return (['-std=%s' % self.std] if self.std else []) + super().get_flags()
