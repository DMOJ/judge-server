from dmoj import judgeenv, executors
from dmoj.testsuite import Tester
from dmoj.utils.ansi import ansi_style


required_executors = ['AWK', 'BF', 'C', 'CPP03', 'CPP11', 'CS', 'GO', 'PERL', 'PY2', 'PY3',
                      'RUBY19', 'RUBY21', 'SED', 'VB']


def main():
    judgeenv.load_env(cli=True, testsuite=True)

    # Emulate ANSI colors with colorama
    __import__('colorama').init()
    executors.load_executors()

    executor_fail = not all(name in executors.executors for name in required_executors)
    if executor_fail:
        print ansi_style('#ansi[A required executor failed to load.](red|bold)')
    else:
        print ansi_style('#ansi[All required executors loaded successfully.](green|bold)')
    print

    tester = Tester(judgeenv.problem_regex, judgeenv.case_regex)
    fails = tester.test_all()
    print
    print 'Test complete'
    if fails:
        print ansi_style('#ansi[A total of %d case(s) failed](red|bold).') % fails
    else:
        print ansi_style('#ansi[All cases passed.](green|bold)')
    raise SystemExit(int(executor_fail or fails != 0))

if __name__ == '__main__':
    main()
