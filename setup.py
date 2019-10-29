# encoding: utf-8
import io
import os
import sys
import traceback
from distutils.errors import DistutilsPlatformError

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext

if os.name == 'nt':
    print('DMOJ is unsupported on Windows.', file=sys.stderr)
    sys.exit(1)

has_pyx = os.path.exists(os.path.join(os.path.dirname(__file__), 'dmoj', 'cptbox', '_cptbox.pyx'))

try:
    with open('/proc/version') as f:
        is_wsl = 'microsoft' in f.read().lower()
except IOError:
    is_wsl = False

# Allow manually disabling seccomp on old kernels. WSL doesn't have seccomp.
has_seccomp = not is_wsl and os.environ.get('DMOJ_USE_SECCOMP') != 'no'

try:
    from Cython.Build import cythonize
except ImportError:
    if has_pyx:
        print('You need to install cython first before installing DMOJ.', file=sys.stderr)
        print('Run: pip install cython', file=sys.stderr)
        print('Or if you do not have pip: easy_install cython', file=sys.stderr)
        sys.exit(1)

    def cythonize(module_list):
        return module_list


class SimpleSharedObject(Extension, object):
    ext_names = set()

    def __init__(self, name, *args, **kwargs):
        super(SimpleSharedObject, self).__init__(name, *args, **kwargs)
        self.ext_names.add(name)
        if '.' in name:
            self.ext_names.add(name.split('.')[-1])


class build_ext_dmoj(build_ext, object):
    def get_ext_filename(self, ext_name):
        if ext_name in SimpleSharedObject.ext_names:
            return ext_name.replace('.', os.sep) + '.so'
        return super(build_ext_dmoj, self).get_ext_filename(ext_name)

    def get_export_symbols(self, ext):
        if isinstance(ext, SimpleSharedObject):
            return ext.export_symbols
        return super(build_ext_dmoj, self).get_export_symbols(ext)

    def run(self):
        try:
            super(build_ext_dmoj, self).run()
        except DistutilsPlatformError as e:
            self.unavailable(e)

    def build_extensions(self):
        arch = os.uname()[4]
        is_arm = arch.startswith('arm') or arch.startswith('aarch')
        target_arch = os.environ.get('DMOJ_TARGET_ARCH')

        extra_compile_args = []
        if is_arm or os.environ.get('DMOJ_REDIST'):
            extra_compile_args.append('-O3')
            if target_arch:
                extra_compile_args.append('-march=%s' % target_arch)
            elif is_arm:
                print('*' * 79)
                print('Building on ARM, specify DMOJ_TARGET_ARCH to CPU-specific arch for GCC!')
                print('Compiling slower generic build.')
                print('*' * 79)
        else:
            extra_compile_args += ['-march=%s' % (target_arch or 'native'), '-O3']
        self.distribution.ext_modules[0].extra_compile_args = extra_compile_args

        super(build_ext_dmoj, self).build_extensions()

    def unavailable(self, e):
        print('*' * 79)
        print('Please procure the necessary *.pyd or *.so files yourself.')
        traceback.print_exc()
        print('*' * 79)


cptbox_sources = ['_cptbox.pyx', 'helper.cpp', 'ptdebug.cpp', 'ptdebug_x86.cpp', 'ptdebug_x64.cpp',
                  'ptdebug_x86_on_x64.cpp', 'ptdebug_x32.cpp', 'ptdebug_arm.cpp', 'ptdebug_arm64.cpp',
                  'ptproc.cpp']

if not has_pyx:
    cptbox_sources[0] = cptbox_sources[0].replace('.pyx', '.cpp')

SOURCE_DIR = os.path.dirname(__file__)
cptbox_sources = [os.path.join(SOURCE_DIR, 'dmoj', 'cptbox', f) for f in cptbox_sources]

libs = ['rt']

if has_seccomp:
    libs += ['seccomp']
if sys.platform.startswith('freebsd'):
    libs += ['procstat']

macros = []
if is_wsl:
    macros.append(('WSL', None))

if not has_seccomp:
    print('*' * 79)
    print('Building without seccomp, expect lower sandbox performance.')
    print('*' * 79)
    macros.append(('PTBOX_NO_SECCOMP', None))

extensions = [Extension('dmoj.checkers._checker', sources=['dmoj/checkers/_checker.c']),
              Extension('dmoj.cptbox._cptbox', sources=cptbox_sources,
                        language='c++', libraries=libs, define_macros=macros),
              SimpleSharedObject('dmoj.utils.setbufsize', sources=['dmoj/utils/setbufsize.c'])]

with io.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    readme = f.read()

setup(
    name='dmoj',
    version='2.0.0',
    packages=find_packages(),
    package_data={
        'dmoj.cptbox': ['syscalls/aliases.list', 'syscalls/*.tbl'],
        'dmoj.executors': ['java_sandbox.jar', '*.policy'],
    },
    entry_points={
        'console_scripts': [
            'dmoj = dmoj.judge:main',
            'dmoj-cli = dmoj.cli:main',
            'dmoj-autoconf = dmoj.executors.autoconfig:main',
        ],
    },
    ext_modules=cythonize(extensions),
    install_requires=['watchdog', 'pyyaml', 'termcolor', 'pygments', 'setproctitle', 'pylru'],
    tests_require=['requests'],
    extras_require={
        'test': ['requests'],
    },
    cmdclass={'build_ext': build_ext_dmoj},

    author='DMOJ Team',
    author_email='contact@dmoj.ca',
    url='https://github.com/DMOJ/judge',
    description='The judge component of the DMOJ: Modern Online Judge platform',
    long_description=readme,
    long_description_content_type='text/markdown',
    keywords='online-judge',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Education',
        'Topic :: Software Development',
    ],
)
