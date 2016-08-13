import os
import re
import traceback
from importlib import import_module

import yaml
import yaml.representer

from dmoj import judgeenv
from dmoj.executors import executors
from dmoj.testsuite import Tester
from dmoj.utils.ansi import ansi_style


def find_directory(parent, expr):
    regex = re.compile(expr)
    for dir in os.listdir(parent):
        if regex.match(dir):
            return os.path.join(parent, dir)

TEST_ON_TRAVIS = ['ADA', 'AWK', 'BF', 'C', 'CBL', 'D', 'CPP03', 'CPP11', 'CLANG', 'CLANGX',
                  'COFFEE', 'GO', 'GROOVY', 'HASK', 'JAVA7', 'JAVA8', 'JAVA9', 'MONOCS',
                  'MONOFS', 'MONOVB', 'PAS', 'GAS32', 'GAS64', 'NASM', 'NASM64',
                  'PERL', 'PHP', 'PY2', 'PY3', 'PYPY', 'PYPY3',
                  'RUBY19', 'RUBY21', 'RUST', 'SCALA', 'SWIFT', 'TEXT']
RVM_DIR = os.path.expanduser('~/.rvm/rubies/')
PYENV_DIR = '/opt/python/'
JVM_DIR = '/usr/lib/jvm/'

OVERRIDES = {
    'PY2': {'py2_home': find_directory(PYENV_DIR, r'2\.7')},
    'RUBY19': {'ruby19_home': find_directory(RVM_DIR, r'ruby-1\.9')},
    'RUBY21': {'ruby21_home': find_directory(RVM_DIR, r'ruby-2\.1')},
    'PYPY': {'pypy_home': find_directory(PYENV_DIR, 'pypy-')},
    'PYPY3': {'pypy3_home': find_directory(PYENV_DIR, 'pypy3-')},
}


def get_dirs(dir):
    try:
        return [item for item in os.listdir(dir) if os.path.isdir(os.path.join(dir, item))]
    except OSError:
        return []


def main():
    result = {}

    judgeenv.env['runtime'] = {}
    judgeenv.env['extra_fs'] = {
        'PHP': ['/etc/php5/', '/etc/terminfo/', '/etc/protocols$'],
        'SWIFT': [os.path.abspath(os.path.join(os.path.dirname(__file__),
                                               re.escape('swift-2.2-SNAPSHOT-2015-12-22-a-ubuntu14.04')))],
    }

    failed = False

    print 'Available JVMs:'
    for jvm in get_dirs(JVM_DIR):
        print '  -', jvm
    print

    print 'Available Pythons:'
    for python in get_dirs(PYENV_DIR):
        print '  -', python
    print

    print 'Available Rubies:'
    for ruby in get_dirs(RVM_DIR):
        print '  -', ruby
    print

    print 'Using extra allowed filesystems:'
    for lang, fs in judgeenv.env['extra_fs'].iteritems():
        print '%-6s: %s' % (lang, '|'.join(fs))
    print

    print 'Testing executors...'

    for name in TEST_ON_TRAVIS:
        executor = import_module('dmoj.executors.' + name)

        print ansi_style('%-34s%s' % ('Testing #ansi[%s](|underline):' % name, '')),

        if not hasattr(executor, 'Executor'):
            failed = True
            print ansi_style('#ansi[Does not export](red|bold) #ansi[Executor](red|underline)')
            continue

        if not hasattr(executor.Executor, 'autoconfig'):
            print ansi_style('#ansi[Could not autoconfig](magenta|bold)')
            continue

        try:
            if name in OVERRIDES:
                print ansi_style('#ansi[(manual config)](yellow)'),
                data = executor.Executor.autoconfig_run_test(OVERRIDES[name])
            else:
                data = executor.Executor.autoconfig()
            config = data[0]
            success = data[1]
            feedback = data[2]
            errors = '' if len(data) < 4 else data[3]
        except Exception:
            failed = True
            print ansi_style('#ansi[Autoconfig broken](red|bold)')
            traceback.print_exc()
        else:
            print ansi_style(['#ansi[%s](red|bold)', '#ansi[%s](green|bold)'][success] %
                             (feedback or ['Failed', 'Success'][success]))

            if success:
                result.update(config)
                executor.Executor.runtime_dict = config
                executors[name] = executor
                for runtime, ver in executor.Executor.get_runtime_versions():
                    print ansi_style('  #ansi[%s](cyan): %s' % (runtime, '.'.join(map(str, ver)) if ver else 'unknown'))
            else:
                if config:
                    print '  Attempted:'
                    print '   ', yaml.dump(config, default_flow_style=False).rstrip().replace('\n', '\n' + ' ' * 4)

                if errors:
                    print '  Errors:'
                    print '   ', errors.replace('\n', '\n' + ' ' * 4)
                failed = True

    print
    print ansi_style('#ansi[Configuration result](green|bold|underline):')
    print yaml.dump({'runtime': result}, default_flow_style=False).rstrip()
    print
    print
    print 'Running test cases...'
    judgeenv.problem_dirs = [os.path.join(os.path.dirname(__file__), 'testsuite')]
    tester = Tester()
    fails = tester.test_all()
    print
    print 'Test complete'
    if fails:
        print ansi_style('#ansi[A total of %d case(s) failed](red|bold).') % fails
    else:
        print ansi_style('#ansi[All cases passed.](green|bold)')
    failed |= fails != 0
    raise SystemExit(int(failed))


if __name__ == '__main__':
    main()
