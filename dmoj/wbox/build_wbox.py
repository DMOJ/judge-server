import os
import sys
import shutil

from distutils.core import Extension
from distutils.command.build_ext import build_ext
from distutils.dist import Distribution
from distutils import log
from distutils.msvccompiler import MSVCCompiler
from distutils.sysconfig import get_config_vars
from Cython.Build import cythonize

if os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))
log.set_verbosity(3)

sources = ['_wbox.pyx', 'handles.cpp', 'process.cpp', 'user.cpp',
           'helpers.cpp', 'firewall.cpp']

distribution = Distribution({
    'ext_modules': cythonize([
        Extension('_wbox', sources=sources, language='c++',
                  libraries=['netapi32', 'advapi32', 'ole32'],
                  define_macros=[('UNICODE', None)])
    ])
})


class Command(build_ext):
    def build_extensions(self):
        self.compiler.initialize()
        if isinstance(self.compiler, MSVCCompiler):
            self.compiler.compile_options.remove('/W3')
            self.compiler.compile_options.remove('/MD')
            if '/GS-' in self.compiler.compile_options:
                self.compiler.compile_options.remove('/GS-')
            self.compiler.compile_options += ['/Ox', '/W4', '/EHsc', '/GL', '/MT']
            self.compiler.ldflags_shared += ['/OPT:REF,ICF', '/LTCG']
        build_ext.build_extensions(self)


command = Command(distribution)
command.finalize_options()
command.run()

# shutil.copy2(command.get_ext_fullpath('_wbox'),
#             command.get_ext_filename('_wbox'))
