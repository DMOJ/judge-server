__executors = ['CPP', 'CPP11', 'JAVA', 'PY2', 'PY3', 'RUBY']
executors = {}


def __load(to_load):
    path = __name__.split('.')[1:]

    def __load_module(executor):
        module = __import__('%s.%s' % (__name__, executor))
        for part in path:
            module = getattr(module, part)
        return module

    for name in to_load:
        executor = __load_module(name)
        if hasattr(executor, 'initialize') and not executor.initialize():
            continue
        executors[name] = executor

__load(__executors)
del __executors, __load
