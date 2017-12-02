# encoding: utf-8
from __future__ import print_function

import os
import sys

if sys.version_info[0] >= 3 and os.name == 'nt':
    print('DMOJ is unsupported on Windows Python 3, please use Python 2 instead.', file=sys.stderr)
    sys.exit(0)

import traceback
import subprocess
from distutils.errors import DistutilsPlatformError
from distutils.msvccompiler import MSVCCompiler

from setuptools import setup, Extension, find_packages
from setuptools.command import build_ext
from setuptools.command.build_ext import build_ext as build_ext_old

has_pyx = os.path.exists(os.path.join(os.path.dirname(__file__), 'dmoj', 'cptbox', '_cptbox.pyx'))

try:
    from Cython.Build import cythonize
except ImportError:
    if has_pyx:
        print('You need to install cython first before installing DMOJ.', file=sys.stderr)
        print('Run: pip install cython', file=sys.stderr)
        print('Or if you do not have pip: easy_install cython', file=sys.stderr)
        sys.exit(1)
    cythonize = lambda x: x


class build_ext_dmoj(build_ext_old):
    def run(self):
        try:
            build_ext_old.run(self)
        except DistutilsPlatformError as e:
            self.unavailable(e)

    def build_extensions(self):
        print(self.compiler)
        if isinstance(self.compiler, MSVCCompiler):
            self.compiler.initialize()
            self.compiler.compile_options.remove('/W3')
            self.compiler.compile_options.remove('/MD')
            if '/GS-' in self.compiler.compile_options:
                self.compiler.compile_options.remove('/GS-')
            self.compiler.compile_options += ['/Ox', '/W4', '/EHsc', '/GL', '/MT']
            self.compiler.ldflags_shared += ['/OPT:REF,ICF', '/LTCG']
        else:
            if os.uname()[4].startswith('arm') or os.environ.get('DMOJ_REDIST'):
                extra_compile_args = ['-O3']
            else:
                extra_compile_args = ['-march=native', '-O3']
            self.distribution.ext_modules[0].extra_compile_args = extra_compile_args

        build_ext_old.build_extensions(self)

    def unavailable(self, e):
        print('*' * 79)
        print('Please procure the necessary *.pyd or *.so files yourself.')
        traceback.print_exc()
        print('*' * 79)


build_ext.build_ext = build_ext_dmoj

wbox_sources = ['_wbox.pyx', 'handles.cpp', 'process.cpp', 'user.cpp', 'helpers.cpp', 'firewall.cpp']
cptbox_sources = ['_cptbox.pyx', 'helper.cpp', 'ptdebug.cpp', 'ptdebug_x86.cpp', 'ptdebug_x64.cpp',
                  'ptdebug_x86_on_x64.cpp', 'ptdebug_x32.cpp', 'ptdebug_arm.cpp', 'ptproc.cpp']

if not has_pyx:
    wbox_sources[0] = wbox_sources[0].replace('.pyx', '.cpp')
    cptbox_sources[0] = cptbox_sources[0].replace('.pyx', '.cpp')

SOURCE_DIR = os.path.dirname(__file__)
wbox_sources = [os.path.join(SOURCE_DIR, 'dmoj', 'wbox', f) for f in wbox_sources]
cptbox_sources = [os.path.join(SOURCE_DIR, 'dmoj', 'cptbox', f) for f in cptbox_sources]

extensions = [Extension('dmoj.checkers._checker', sources=['dmoj/checkers/_checker.c'])]
if os.name == 'nt' or 'sdist' in sys.argv:
    extensions += [Extension('dmoj.wbox._wbox', sources=wbox_sources, language='c++',
                             libraries=['netapi32', 'advapi32', 'ole32'],
                             define_macros=[('UNICODE', None)])]

if os.name != 'nt' or 'sdist' in sys.argv:
    libs = ['rt']
    if sys.platform.startswith('freebsd'):
        libs += ['procstat']

    macros = []
    try:
        with open('/proc/version') as f:
            if 'microsoft' in f.read().lower():
                macros.append(('WSL', None))
    except IOError:
        pass
    extensions += [Extension('dmoj.cptbox._cptbox', sources=cptbox_sources,
                             language='c++', libraries=libs, define_macros=macros)]

rst_path = os.path.join(os.path.dirname(__file__), 'README.rst')

if 'sdist' in sys.argv:
    readme = subprocess.check_output("pandoc -f markdown_github README.md -t html | sed -e 's/❌/X/g' | "
                                     'pandoc -f html -t rst --columns=300', shell=True)
    with open(rst_path, 'w') as f:
        f.write(readme)
else:
    try:
        with open(rst_path) as f:
            readme = f.read()
    except IOError:
        readme = None

setup(
    name='dmoj',
    version='1.0.4',
    packages=find_packages(),
    package_data={
        'dmoj.cptbox': ['syscalls/aliases.list', 'syscalls/*.tbl'],
        'dmoj.executors': ['csbox.exe', 'java-sandbox.jar', '*.policy'],
        'dmoj.wbox': ['getaddr*.exe', 'dmsec*.dll'],
    },
    entry_points={
        'console_scripts': [
            'dmoj = dmoj.judge:main',
            'dmoj-cli = dmoj.cli:main',
            'dmoj-autoconf = dmoj.executors.autoconfig:main',
        ],
    },
    ext_modules=cythonize(extensions),
    install_requires=['watchdog', 'pyyaml', 'ansi2html', 'termcolor', 'pygments', 'six'],
    tests_require=['mock', 'requests'],
    extras_require={
        'test': ['mock'],
    },

    author='quantum5, Xyene',
    author_email='admin@dmoj.ca',
    url='https://github.com/DMOJ/judge',
    description='The judge component of the DMOJ: Modern Online Judge platform',
    long_description=readme,
    keywords='online-judge',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Education',
        'Topic :: Software Development',
    ],
)
