from .GCCExecutor import GCCExecutor
from judgeenv import env


class Executor(GCCExecutor):
    command = env['runtime'].get('g++')
    std = None
    ext = '.cpp'
    name = 'CPP'
    test_program = '''
#include <iostream>

int main() {
    std::cout << std::cin.rdbuf();
    return 0;
}
'''

    def get_flags(self):
        return (['-std=%s' % self.std] if self.std else []) + super(Executor, self).get_flags()

initialize = Executor.initialize
