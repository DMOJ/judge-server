import os
import sys
import shutil

from distutils.core import Extension
from distutils.command.build_ext import build_ext
from distutils.dist import Distribution
from distutils.msvccompiler import MSVCCompiler
from distutils import log

if os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))
log.set_verbosity(3)

distribution = Distribution({
    'ext_modules': [Extension('_debugger', sources=['_debugger.cpp'])]
})


class Command(build_ext):
    def build_extensions(self):
        if os.uname()[4].startswith('arm') or 'redist' in sys.argv:
            extra_compile_args = ['-O3']
        else:
            extra_compile_args = ['-march=native', '-O3']
        self.distribution.ext_modules[0].extra_compile_args = extra_compile_args

        build_ext.build_extensions(self)


command = Command(distribution)
command.finalize_options()
command.run()

shutil.copy2(command.get_ext_fullpath('_debugger'), command.get_ext_filename('_debugger'))
