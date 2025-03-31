import logging
import platform

from dmoj import judgeenv
from dmoj.citest import ci_test
from dmoj.executors import get_available

arch = platform.machine()
ALLOW_FAIL = {'GASARM', 'SWIFT'}
EXECUTORS = get_available()

if arch == 'aarch64':
    ALLOW_FAIL -= {'GASARM'}
    ALLOW_FAIL |= {'D', 'GAS32', 'GAS64', 'LEAN4', 'NASM', 'NASM64', 'TUR'}
elif arch != 'x86_64':
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
