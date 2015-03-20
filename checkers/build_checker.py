from distutils.core import Extension
from distutils.command.build_ext import build_ext
from distutils.dist import Distribution
from distutils import log

import os
import shutil

if os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))
log.set_verbosity(3)

distribution = Distribution({
    'ext_modules': [Extension('_checker', sources=['_checker.c'])]
})

command = build_ext(distribution)
command.finalize_options()
command.run()

shutil.copy2(command.get_ext_fullpath('_checker'),
             command.get_ext_filename('_checker'))
