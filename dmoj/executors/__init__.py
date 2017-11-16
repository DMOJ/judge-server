from __future__ import print_function

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


def get_available():
    to_load = set(i.group(1) for i in map(_reexecutor.match,
                                          os.listdir(os.path.dirname(__file__)))
                  if i is not None)
    if only_executors:
        to_load &= only_executors
    if exclude_executors:
        to_load -= exclude_executors
    to_load -= _unsupported_executors
    to_load = sorted(to_load)
    return to_load


def load_executor(name):
    try:
        return import_module('%s.%s' % (__name__, name))
    except ImportError as e:
        # Python 2 has no quotes, Python 3 has quotes :|
        if str(e).replace("'", '') not in ('No module named _cptbox',
                                           'No module named msvcrt',
                                           'No module named _wbox',
                                           'No module named termios'):
            traceback.print_exc()


def load_executors():
    to_load = get_available()

    print('Self-testing executors...')

    for name in to_load:
        executor = load_executor(name)

        if executor is None or not hasattr(executor, 'Executor'):
            continue

        cls = executor.Executor
        if hasattr(cls, 'initialize') and not cls.initialize(sandbox=env.selftest_sandboxing):
            continue

        if hasattr(executor, 'aliases'):
            for alias in executor.aliases():
                if alias not in _unsupported_executors:
                    executors[alias] = executor
        else:
            executors[name] = executor

    print
