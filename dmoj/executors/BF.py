import itertools

import six
from six.moves import map

from dmoj.executors.C import Executor as CExecutor
from dmoj.error import CompileError

template = b'''\
#define _GNU_SOURCE
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>

int main(int argc, char **argv) {
    char *p;
    size_t size;

    errno = 0;
    if (argc != 2 || (size = strtoull(argv[1], NULL, 10), errno)) {
        fprintf(stderr, "%s <bytes to allocate>\\n", argv[0]);
        return 2;
    }

    p = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) {
        perror("mmap");
        return 2;
    }

    {code}
}
'''

trans = {b'>': b'++p;', b'<': b'--p;',
         b'+': b'++*p;', b'-': b'--*p;',
         b'.': b'putchar(*p);', b',': b'*p=getchar();',
         b'[': b'while(*p){', b']': b'}'}

if six.PY3:
    trans = {k[0]: v for k, v in trans.items()}


class Executor(CExecutor):
    name = 'BF'
    test_program = ',+[-.,+]'

    def __init__(self, problem_id, source_code, **kwargs):
        if source_code.count(b'[') != source_code.count(b']'):
            raise CompileError(b'Unmatched brackets\n')
        code = template.replace(b'{code}', b''.join(map(trans.get, source_code, itertools.repeat(b''))))
        super(Executor, self).__init__(problem_id, code, **kwargs)

    def launch(self, *args, **kwargs):
        memory = kwargs['memory']
        # For some reason, RLIMIT_DATA is being applied to our mmap, so we have to increase the memory limit.
        kwargs['memory'] += 8192
        return super(Executor, self).launch(str(memory * 1024), **kwargs)

    @classmethod
    def get_runtime_versions(cls):
        return ('bf', (1, 33, 7)),
