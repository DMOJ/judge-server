import types
from pathlib import Path
from typing import Any, Optional, Union


def load_module(name: str, code: str, filename: Optional[Union[str, Path]] = None) -> Any:
    mod = types.ModuleType(name)
    if filename is not None:
        mod.__file__ = str(filename)
    exec(compile(code, filename or '<string>', 'exec'), mod.__dict__)
    return mod


def load_module_from_file(filename: Union[str, Path]) -> Any:
    filename = Path(filename).resolve(strict=True)
    name = filename.stem

    with open(filename) as f:
        return load_module(name, f.read(), filename)
