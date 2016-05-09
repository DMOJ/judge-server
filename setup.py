import os
import sys
import traceback
from distutils.errors import DistutilsPlatformError
from distutils.msvccompiler import MSVCCompiler

from setuptools import setup, Extension
from setuptools.command import build_ext
from setuptools.command.build_ext import build_ext as build_ext_old

try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None


class build_ext_dmoj(build_ext_old):
    def run(self):
        try:
            build_ext_old.run(self)
        except DistutilsPlatformError as e:
            self.unavailable(e)

    def build_extensions(self):
        if isinstance(self.compiler, MSVCCompiler):
            self.compiler.initialize()
            self.compiler.compile_options.remove('/W3')
            self.compiler.compile_options.remove('/MD')
            if '/GS-' in self.compiler.compile_options:
                self.compiler.compile_options.remove('/GS-')
            self.compiler.compile_options += ['/Ox', '/W4', '/EHsc', '/GL', '/MT']
            self.compiler.ldflags_shared += ['/OPT:REF,ICF', '/LTCG']
        else:
            if os.uname()[4].startswith('arm') or 'redist' in sys.argv:
                extra_compile_args = ['-O3']
            else:
                extra_compile_args = ['-march=native', '-O3']
            self.distribution.ext_modules[0].extra_compile_args = extra_compile_args

        build_ext_old.build_extensions(self)

    def unavailable(self, e):
        print '*' * 79
        print 'Please procure the necessary *.pyd or *.so files yourself.'
        traceback.print_exc()
        print '*' * 79


build_ext.build_ext = build_ext_dmoj

extensions = [Extension('dmoj.checkers._checker', sources=['dmoj/checkers/_checker.c'])]
wbox_sources = ['_wbox.cpp' if cythonize is None else '_wbox.pyx',
                'handles.cpp', 'process.cpp', 'user.cpp', 'helpers.cpp', 'firewall.cpp']
cptbox_sources = ['_cptbox.cpp' if cythonize is None else '_cptbox.pyx',
                  'ptdebug.cpp', 'ptdebug_x86.cpp', 'ptdebug_x64.cpp',
                  'ptdebug_x86_on_x64.cpp', 'ptdebug_x32.cpp', 'ptdebug_arm.cpp', 'ptproc.cpp']

SOURCE_DIR = os.path.dirname(__file__)
wbox_sources = [os.path.join(SOURCE_DIR, 'dmoj', 'wbox', file) for file in wbox_sources]
cptbox_sources = [os.path.join(SOURCE_DIR, 'dmoj', 'cptbox', file) for file in cptbox_sources]

if os.name == 'nt':
    extensions += [Extension('dmoj.wbox._wbox', sources=wbox_sources, language='c++',
                             libraries=['netapi32', 'advapi32', 'ole32'],
                             define_macros=[('UNICODE', None)])]
else:
    extensions += [Extension('dmoj.cptbox._cptbox', sources=cptbox_sources,
                             language='c++', libraries=['rt'])]

setup(
    name='dmoj',
    version='0.1',
    packages=['dmoj'],
    entry_points={
        'console_scripts': [
            'dmoj = dmoj.judge:main',
            'dmoj-cli = dmoj.cli:main',
        ]
    },
    ext_modules=extensions if cythonize is None else cythonize(extensions),
    install_requires=['watchdog', 'pyyaml', 'ansi2html', 'termcolor'],

    author='quantum5',
    author_email='quantum2048@gmail.com',
    url='https://github.com/DMOJ/judge',
    description='The judge component of the Don Mills Online Judge platform',
    keywords='online-judge',
    classifiers=[
        'Development Status :: 3 - Beta',
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
