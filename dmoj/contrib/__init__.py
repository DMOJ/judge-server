import os
import re
from typing import Any, Dict, List, TYPE_CHECKING

from dmoj.utils.load import get_available_modules, load_module, load_modules

_recontribmodule = re.compile(r'([a-z]+)\.py')

contrib_modules: Dict[str, Any] = {}


def get_available() -> List[str]:
    return get_available_modules(_recontribmodule, os.path.dirname(__file__), None, None)


def load_contrib_module(name: str) -> Any:
    return load_module(f'{__name__}.{name}', ())


def load_contrib_modules() -> None:
    load_modules(get_available(), load_contrib_module, 'ContribModule', contrib_modules, set())
