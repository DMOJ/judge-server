from .GCCExecutor import make_executor
from .utils import test_executor
from error import CompileError
from judgeenv import env
import os
import itertools

OldExecutor, _ = make_executor('C', 'gcc', ['-std=c99'], '.c', None)

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


class Executor(OldExecutor):
    def __init__(self, problem_id, source_code):
        if source_code.count('[') != source_code.count(']'):
            raise CompileError('Unmatched brackets')
        code = template % (''.join(itertools.imap(trans.get, source_code, itertools.repeat(''))))
        super(Executor, self).__init__(problem_id, code)


def initialize():
    if 'gcc' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['gcc']):
        return False
    return test_executor('BF', Executor, '''\
++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->+>+[<]<-]>>.>---.+++++++..+++.>>++++.
------------.<-.<.+++.------.--------.>>+.>++.
''')


del make_executor
