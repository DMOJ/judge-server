import itertools

import six
from six.moves import map

from dmoj.executors.C import Executor as CExecutor
from dmoj.error import CompileError

template = b'''\
#include <stdio.h>

char array[16777216];

int main() {
    char *ptr = array;
    %s
}
'''

trans = {b'>': b'++ptr;', b'<': b'--ptr;',
         b'+': b'++*ptr;', b'-': b'--*ptr;',
         b'.': b'putchar(*ptr);', b',': b'*ptr=getchar();',
         b'[': b'while(*ptr){', b']': b'}'}

if six.PY3:
    trans = {k[0]: v for k, v in trans.items()}


class Executor(CExecutor):
    name = 'BF'
    test_program = ',+[-.,+]'

    def __init__(self, problem_id, source_code, **kwargs):
        if source_code.count(b'[') != source_code.count(b']'):
            raise CompileError(b'Unmatched brackets\n')
        code = template.replace(b'%s', b''.join(map(trans.get, source_code, itertools.repeat(b''))))
        super(Executor, self).__init__(problem_id, code, **kwargs)

    @classmethod
    def get_runtime_versions(cls):
        return ('bf', (1, 33, 7)),
