__executors = ['TUR', 'OCAML', 'C', 'CPP', 'CPP0X', 'CPP11', 'CS', 'FS', 'MONOCS', 'JAVA', 'PY2', 'PY3', 'PYPY',
               'PYPY3', 'PAS', 'PERL', 'RUBY18', 'RUBY19', 'RUBY21', 'HASK', 'GO', 'F95', 'NASM', 'PHP', 'LUA']
executors = {}


def __load(to_load):
    import traceback

    path = __name__.split('.')[1:]

    def __load_module(executor):
        try:
            module = __import__('%s.%s' % (__name__, executor))
        except ImportError as e:
            if e.message != 'No module named _cptbox':
                traceback.print_exc()
            return None
        for part in path:
            module = getattr(module, part)
        return getattr(module, executor)

    for name in to_load:
        executor = __load_module(name)
        if executor is None:
            continue
        if hasattr(executor, 'initialize') and not executor.initialize():
            continue
        if hasattr(executor, 'aliases'):
            for alias in executor.aliases():
                executors[alias] = executor
        else:
            executors[name] = executor


__load(__executors)
del __executors, __load
