import os
import imp


def load_module_from_file(filename):
    path, name = os.path.split(filename)
    name, ext = os.path.splitext(name)

    mod = imp.new_module(name)
    mod.__file__ = os.path.abspath(filename)
    exec compile(open(mod.__file__).read(), mod.__file__, 'exec') in mod.__dict__
    return mod
