import os
import re
import traceback
from distutils.version import LooseVersion
from importlib import import_module

import yaml
import yaml.representer

from dmoj import judgeenv
from dmoj.executors import executors
from dmoj.testsuite import Tester
from dmoj.utils.ansi import ansi_style


def find_directory(parent, expr):
    regex = re.compile(expr)
    dirs = [dir for dir in os.listdir(parent) if regex.match(dir)]
    if not dirs:
        return
    return os.path.join(parent, max(dirs, key=LooseVersion))


def make_override(home, parent, expr):
    directory = find_directory(parent, expr)
    if not directory:
        return
    return {home: directory}


TEST_ON_TRAVIS = ['ADA', 'AWK', 'BF', 'C', 'CBL', 'D', 'DART', 'CPP0X', 'CPP03', 'CPP11', 'CLANG', 'CLANGX',
                  'F95', 'GO', 'GROOVY', 'HASK', 'JAVA7', 'JAVA8', 'JAVA9',
                  'PAS', 'PRO', 'GAS32', 'GAS64', 'LUA', 'NASM', 'NASM64',
                  'PERL', 'PHP', 'PY2', 'PY3', 'PYPY', 'PYPY3',
                  'RUBY2', 'RUST', 'SCM', 'SED', 'SWIFT', 'TCL', 'TEXT']
RVM_DIR = os.path.expanduser('~/.rvm/rubies/')
PYENV_DIR = '/opt/python/'
JVM_DIR = '/usr/lib/jvm/'

OVERRIDES = {
    'PY2':    make_override('py2_home',    PYENV_DIR, r'2\.'),
    'PY3':    make_override('py3_home',    PYENV_DIR, r'3\.'),
    'RUBY2':  make_override('ruby2_home',  RVM_DIR,   r'ruby-2\.'),
    'PYPY':  {'pypy_home':  os.path.abspath('pypy2')},
    'PYPY3': {'pypy3_home': os.path.abspath('pypy3')},
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
        'SWIFT': [os.path.abspath(os.path.join(os.path.dirname(__file__), 'swift'))],
        'RUBY2': ['/home/travis/.gem/'],
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
                if not OVERRIDES[name]:
                    print ansi_style('#ansi[Environment not found on Travis](red)')
                    continue
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
                if feedback == 'Could not find JVM':
                    continue

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
    if failed:
        print ansi_style('#ansi[Executor configuration failed.](red|bold).')
    else:
        print ansi_style('#ansi[Executor configuration succeeded.](green|bold).')
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
