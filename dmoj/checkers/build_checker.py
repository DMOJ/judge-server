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
    'ext_modules': [Extension('_checker', sources=['_checker.c'])]
})


class Command(build_ext):
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

        build_ext.build_extensions(self)

command = Command(distribution)
command.finalize_options()
command.run()

shutil.copy2(command.get_ext_fullpath('_checker'),
             command.get_ext_filename('_checker'))
