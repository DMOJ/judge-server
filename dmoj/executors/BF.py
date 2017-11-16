import itertools

from dmoj.executors.C import Executor as CExecutor
from dmoj.error import CompileError


template = '''\
#include <stdio.h>

char array[16777216];

int main() {
    char *ptr = array;
    %s
}
'''

trans = {'>': '++ptr;', '<': '--ptr;',
         '+': '++*ptr;', '-': '--*ptr;',
         '.': 'putchar(*ptr);', ',': '*ptr=getchar();',
         '[': 'while(*ptr){', ']': '}'}


class Executor(CExecutor):
    name = 'BF'
    test_program = ',+[-.,+]'

    def __init__(self, problem_id, source_code, **kwargs):
        if source_code.count('[') != source_code.count(']'):
            raise CompileError('Unmatched brackets\n')
        code = template % (''.join(map(trans.get, source_code, itertools.repeat(''))))
        super(Executor, self).__init__(problem_id, code, **kwargs)

    @classmethod
    def get_runtime_versions(cls):
        return ('bf', (1, 33, 7)),
