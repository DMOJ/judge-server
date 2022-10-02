import os
import re
from typing import Any, Dict

from dmoj.judgeenv import exclude_executors, only_executors
from dmoj.utils.load import get_available_modules, load_module, load_modules

_reexecutor = re.compile(r'([A-Z0-9]+)\.py$')

# List of executors that exist for historical purposes, but which shouldn't ever be run on a normal system
# We keep them for compatibility purposes, but they are not important enough to have a commandline flag for enabling
# them; instead, removing them from this list suffices.
_unsupported_executors = {'BASH', 'COFFEE'}

executors: Dict[str, Any] = {}


def by_ext(ext: str) -> Any:
    ext = ext.lower()

    for name, executor in executors.items():
        if name.lower() == ext:
            return executor

    for executor in sorted(executors.values(), key=lambda executor: executor.Executor.name):
        if executor.Executor.ext == ext:
            return executor

    raise KeyError('no executor for extension "%s"' % ext)


def from_filename(filename: str) -> Any:
    _, _, ext = filename.partition('.')
    if not ext:
        raise KeyError('invalid file name')

    return by_ext(ext)


def get_available():
    return get_available_modules(
        _reexecutor, os.path.dirname(__file__), only_executors, exclude_executors | _unsupported_executors
    )


def load_executor(name):
    return load_module('%s.%s' % (__name__, name), ('No module named "_cptbox"', 'No module named "termios"'))


def load_executors():
    from dmoj.judgeenv import skip_self_test

    load_modules(
        get_available(),
        load_executor,
        'Executor',
        executors,
        _unsupported_executors,
        loading_message='Skipped self-tests' if skip_self_test else 'Self-testing executors',
    )
