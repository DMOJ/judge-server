from typing import List, Optional

from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'g++'
    std: Optional[str] = None
    ext = 'cpp'
    name = 'CPP03'
    test_program = """
#include <iostream>

int main() {
    std::cout << std::cin.rdbuf();
    return 0;
}
"""

    def get_flags(self) -> List[str]:
        return ([f'-std={self.std}'] if self.std else []) + super().get_flags()
