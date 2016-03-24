import os
import sys
import shutil
from distutils import log
from distutils.command.build_ext import build_ext
from distutils.core import Extension
from distutils.dist import Distribution
from distutils.sysconfig import get_config_vars

try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

if os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))
log.set_verbosity(3)

opt, = get_config_vars('OPT')
os.environ['OPT'] = ' '.join(flag for flag in opt.split() if flag != '-Wstrict-prototypes')

extra_compile_args = ['-O3', '-std=c++11']
if not os.uname()[4].startswith('arm') and 'redist' not in sys.argv:
    extra_compile_args += ['-march=native']

sources = ['ptdebug.cpp', 'ptdebug_x86.cpp', 'ptdebug_x64.cpp',
           'ptdebug_x86_on_x64.cpp', 'ptdebug_x32.cpp', 'ptdebug_arm.cpp', 'ptproc.cpp']

if cythonize is None:
    if os.path.exists('_cptbox.cpp'):
        sources.insert(0, '_cptbox.cpp')
    else:
        print 'You need to have either cython or _cptbox.cpp prebuilt.'
        raise SystemExit(1)
else:
    sources.insert(0, '_cptbox.pyx')

ext_modules = [Extension('_cptbox', sources=sources,
                         language='c++', libraries=['rt'],
                         extra_compile_args=extra_compile_args)]

if cythonize is not None:
    ext_modules = cythonize(ext_modules)

distribution = Distribution({
    'ext_modules': ext_modules
})

command = build_ext(distribution)
command.finalize_options()
command.run()

shutil.copy2(command.get_ext_fullpath('_cptbox'),
             command.get_ext_filename('_cptbox'))
