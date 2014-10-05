__author__ = 'Quantum'

import os


class path(str):
    def __new__(cls, *args):
        return str.__new__(cls, os.path.join(*args))

    def __div__(self, other):
        return path(self, other)

    __truediv__ = __div__
    __floordiv__ = __div__
