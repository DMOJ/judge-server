import os
import types
from typing import Any, Optional


def load_module(name: str, code: str, filename: Optional[str] = None) -> Any:
    mod = types.ModuleType(name)
    if filename is not None:
        mod.__file__ = filename
    exec(compile(code, filename or '<string>', 'exec'), mod.__dict__)
    return mod


def load_module_from_file(filename: str) -> Any:
    path, name = os.path.split(filename)
    name, ext = os.path.splitext(name)

    with open(filename) as f:
        return load_module(name, f.read(), os.path.abspath(filename))
