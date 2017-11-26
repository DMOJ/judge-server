from .gcc_executor import GCCExecutor


class Executor(GCCExecutor):
    command = 'g++'
    std = None
    ext = '.cpp'
    name = 'CPP03'
    test_program = '''
#include <iostream>

int main() {
    std::cout << std::cin.rdbuf();
    return 0;
}
'''

    def get_flags(self):
        return (['-std=%s' % self.std] if self.std else []) + super(Executor, self).get_flags()
