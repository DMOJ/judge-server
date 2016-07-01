import os
import re
import traceback
from importlib import import_module

from dmoj.judgeenv import env, only_executors, exclude_executors

_reexecutor = re.compile('([A-Z0-9]+)\.py$')

# List of executors that exist for historical purposes, but which shouldn't ever be run on a normal system
# We keep them for compatibility purposes, but they are not important enough to have a commandline flag for enabling
# them; instead, removing them from this list suffices.
_unsupported_executors = {'CPP0X'}

executors = {}


def load_executors():
    to_load = set(i.group(1) for i in map(_reexecutor.match,
                                          os.listdir(os.path.dirname(__file__)))
                  if i is not None)

    if only_executors:
        to_load &= only_executors
    if exclude_executors:
        to_load -= exclude_executors
    to_load -= _unsupported_executors
    to_load = sorted(to_load)

    print 'Self-testing executors...'

    for name in to_load:
        try:
            executor = import_module('%s.%s' % (__name__, name))
        except ImportError as e:
            if e.message not in ('No module named _cptbox',
                                 'No module named msvcrt',
                                 'No module named _wbox',
                                 'No module named termios'):
                traceback.print_exc()
            continue

        if not hasattr(executor, 'Executor'):
            continue

        cls = executor.Executor
        if hasattr(cls, 'initialize') and not cls.initialize(sandbox=env.get('selftest_sandboxing', True)):
            continue

        if hasattr(executor, 'aliases'):
            for alias in executor.aliases():
                if alias not in _unsupported_executors:
                    executors[alias] = cls
        else:
            executors[name] = cls

    print
