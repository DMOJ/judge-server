import logging
import os

from dmoj import judgeenv
from dmoj.citest import ci_test, get_dirs, make_override

EXECUTORS = ['ADA', 'AWK', 'BF', 'C', 'CBL', 'D', 'DART', 'CPP03', 'CPP11', 'CLANG', 'CLANGX',
             'F95', 'GO', 'GROOVY', 'HASK', 'JAVA8', 'OCAML', 'SCALA', 'MONOCS', 'MONOVB',
             'PAS', 'PRO', 'GAS32', 'GAS64', 'LUA', 'NASM', 'NASM64',
             'PERL', 'PHP', 'PY2', 'PY3', 'PYPY', 'PYPY3', 'RKT',
             'RUBY2', 'RUST', 'SCM', 'SED', 'SWIFT', 'SBCL', 'TCL', 'TEXT']

RVM_DIR = os.path.expanduser('~/.rvm/rubies/')
PYENV_DIR = '/opt/python/'
JVM_DIR = '/usr/lib/jvm/'

OVERRIDES = {
    'PY2': make_override('py2_home', PYENV_DIR, r'2\.'),
    'PY3': make_override('py3_home', PYENV_DIR, r'3\.'),
    'RUBY2': make_override('ruby2_home', RVM_DIR, r'ruby-2\.'),
    'PYPY': {'pypy_home': os.path.abspath('pypy2')},
    'PYPY3': {'pypy3_home': os.path.abspath('pypy3')},
    'PHP': {'php': '/usr/bin/php'},
}


def main():
    logging.basicConfig(level=logging.INFO)

    judgeenv.env['runtime'] = {}
    judgeenv.env['extra_fs'] = {
        'PHP': ['/etc/php5/', '/etc/terminfo/', '/etc/protocols$'],
        'SWIFT': [os.path.abspath(os.path.join(os.path.dirname(__file__), 'swift'))],
        'RUBY2': ['/home/travis/.gem/'],
    }

    print('Available JVMs:')
    for jvm in get_dirs(JVM_DIR):
        print('  -', jvm)
    print()

    print('Available Pythons:')
    for python in get_dirs(PYENV_DIR):
        print('  -', python)
    print()

    print('Available Rubies:')
    for ruby in get_dirs(RVM_DIR):
        print('  -', ruby)
    print()

    print('Using extra allowed filesystems:')
    for lang, fs in judgeenv.env['extra_fs'].iteritems():
        print('%-6s: %s' % (lang, '|'.join(fs)))
    print()

    print('Testing executors...')

    ci_test(EXECUTORS, OVERRIDES)


if __name__ == '__main__':
    main()
