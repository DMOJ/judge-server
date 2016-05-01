import os
import sys

__author__ = 'Quantum'


def make_unicode_path(s):
    if not isinstance(s, unicode):
        return unicode(s, sys.getfilesystemencoding())
    return s


class path(unicode):
    def __new__(cls, *args):
        return unicode.__new__(cls, os.path.join(*[make_unicode_path(i) for i in args]))

    def __div__(self, other):
        return path(self, other)

    __truediv__ = __div__
    __floordiv__ = __div__
