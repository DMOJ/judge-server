import os
import re
from judgeenv import env

_reexecutor = re.compile('([A-Z0-9]+)\.py$')
__executors = [i.group(1) for i in map(_reexecutor.match,
                                       os.listdir(os.path.dirname(__file__)))
               if i is not None]
__executors.sort()

executors = {}

def __load(to_load):
    import traceback

    path = __name__.split('.')[1:]

    def __load_module(executor):
        try:
            module = __import__('%s.%s' % (__name__, executor))
        except ImportError as e:
            if e.message not in ('No module named _cptbox',
                                 'No module named msvcrt',
                                 'No module named _wbox'):
                traceback.print_exc()
            return None
        for part in path:
            module = getattr(module, part)
        return getattr(module, executor)

    for name in to_load:
        executor = __load_module(name)
        if executor is None:
            continue
        if hasattr(executor, 'initialize') and not executor.initialize(sandbox=env.get('selftest_sandboxing', True)):
            continue
        if hasattr(executor, 'aliases'):
            for alias in executor.aliases():
                executors[alias] = executor
        else:
            executors[name] = executor


__load(__executors)
del __executors, __load
