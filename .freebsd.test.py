from dmoj import judgeenv
from dmoj.citest import ci_test

EXECUTORS = ['AWK', 'BF', 'C', 'CPP03', 'CPP11', 'CLANG', 'CLANGX',
             'JAVA8', 'PERL', 'PY2', 'PY3', 'RUBY2', 'SED', 'TEXT']
OVERRIDES = {}


def main():
    judgeenv.env['runtime'] = {}
    judgeenv.env['extra_fs'] = {
        'PERL': ['/dev/dtrace/helper$', '/dev/hv_tsc$'],
        'PY3': ['/dev/hv_tsc$'],
        'RUBY2': ['/dev/dtrace/helper$'],
    }

    print 'Using extra allowed filesystems:'
    for lang, fs in judgeenv.env['extra_fs'].iteritems():
        print '%-6s: %s' % (lang, '|'.join(fs))
    print

    print 'Testing executors...'

    ci_test(EXECUTORS, OVERRIDES)


if __name__ == '__main__':
    main()
