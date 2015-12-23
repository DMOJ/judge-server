import os
import shutil
from distutils.core import Extension
from distutils.command.build_ext import build_ext
from distutils.dist import Distribution
from distutils import log
from distutils.sysconfig import get_config_vars

from Cython.Build import cythonize


if os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))
log.set_verbosity(3)

opt, = get_config_vars('OPT')
os.environ['OPT'] = ' '.join(flag for flag in opt.split() if flag != '-Wstrict-prototypes')
extra_compile_args = ['-march=native', '-O3']

sources = ['_cptbox.pyx', 'ptdebug.cpp', 'ptdebug_x86.cpp', 'ptdebug_x64.cpp',
           'ptdebug_x86_on_x64.cpp', 'ptproc.cpp']

distribution = Distribution({
    'ext_modules': cythonize([Extension('_cptbox', sources=sources,
                                        language='c++', libraries=['rt'],
                                        extra_compile_args=extra_compile_args)])
})

command = build_ext(distribution)
command.finalize_options()
command.run()

shutil.copy2(command.get_ext_fullpath('_cptbox'),
             command.get_ext_filename('_cptbox'))
