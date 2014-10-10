import os
import imp
import sys


def load_module_from_file(filename, namespace):
    path, name = os.path.split(filename)
    name, ext = os.path.splitext(name)

    modname = '%s_%s' % (namespace, name)

    imp.acquire_lock()
    try:
        file, filename, data = imp.find_module(name, [path])
        old_mod = sys.modules.get(modname, None)
        mod = imp.load_module(modname, file, filename, data)
        if old_mod is None:
            del sys.modules[modname]
        else:
            sys.modules[modname] = old_mod
        return mod
    finally:
        imp.release_lock()
