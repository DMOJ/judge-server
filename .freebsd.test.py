import logging

from dmoj import judgeenv
from dmoj.citest import ci_test

EXECUTORS = [
    'AWK',
    'BF',
    'C',
    'C11',
    'CPP03',
    'CPP11',
    'CPP14',
    'CPP17',
    'CLANG',
    'CLANGX',
    'JAVA8',
    'MONOCS',
    'MONOFS',
    'MONOVB',
    'PAS',
    'PERL',
    'PY2',
    'PY3',
    'RUBY2',
    'SED',
    'TEXT',
]
OVERRIDES = {}


def main():
    judgeenv.env['runtime'] = {}
    judgeenv.env['extra_fs'] = {
        'PERL': [{'exact_file': '/dev/dtrace/helper'}],
        'RUBY2': [{'exact_file': '/dev/dtrace/helper'}],
    }

    logging.basicConfig(level=logging.INFO)

    print('Using extra allowed filesystems:')
    for lang, fs in judgeenv.env['extra_fs'].iteritems():
        for rules in fs:
            for access_type, file in rules.iteritems():
                print('%-6s: %s: %s' % (lang, access_type, file))
    print()

    print('Testing executors...')
    ci_test(EXECUTORS, OVERRIDES)


if __name__ == '__main__':
    main()
