__executors = ['C', 'CPP', 'CPP0X', 'CPP11', 'CS', 'JAVA', 'PY2', 'PY3', 'PAS', 'PERL', 'RUBY18', 'RUBY19', 'HASK']
executors = {}


def __load(to_load):
    path = __name__.split('.')[1:]

    def __load_module(executor):
        module = __import__('%s.%s' % (__name__, executor))
        for part in path:
            module = getattr(module, part)
        return getattr(module, executor)

    for name in to_load:
        executor = __load_module(name)
        if hasattr(executor, 'initialize') and not executor.initialize():
            continue
        if hasattr(executor, 'aliases'):
            for alias in executor.aliases():
                executors[alias] = executor
        else:
            executors[name] = executor


__load(__executors)
del __executors, __load
