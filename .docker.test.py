import logging
import os

from dmoj import judgeenv
from dmoj.citest import ci_test
from dmoj.executors import get_available

arch = os.getenv('ARCH', 'amd64')
if arch == 'amd64':
    ALLOW_FAIL = {'GASARM', 'JAVA9', 'JAVA10', 'OBJC'}
    EXECUTORS = get_available()
elif arch == 'aarch64':
    EXECUTORS = {'AWK', 'BF', 'C', 'C11', 'CPP03', 'CPP11', 'CPP14', 'CPP17',
                 'JAVA8', 'JAVA11', 'PAS', 'PERL', 'PY2', 'PY3', 'SED', 'TEXT'}
    ALLOW_FAIL = set()
else:
    raise AssertionError('invalid architecture')

OVERRIDES = {}


def main():
    logging.basicConfig(level=logging.INFO)

    judgeenv.env['runtime'] = {}
    judgeenv.env['extra_fs'] = {}

    print('Testing executors...')

    ci_test(EXECUTORS, OVERRIDES, ALLOW_FAIL)


if __name__ == '__main__':
    main()
