import os

from dmoj.wbox.sandbox import WBoxPopen

_dir = os.path.dirname(__file__)

default_inject32 = os.path.abspath(os.path.join(_dir, u'dmsec32.dll'))
default_inject64 = os.path.abspath(os.path.join(_dir, u'dmsec64.dll'))
default_inject_func = 'InjectMain'

del os
