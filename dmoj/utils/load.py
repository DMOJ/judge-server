import os
import traceback
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Pattern, Sequence, Set


def get_available_modules(
    pattern: Pattern, dirname: str, only: Optional[Set[str]] = None, exclude: Optional[Set[str]] = None
) -> List[str]:
    to_load = {i.group(1) for i in map(pattern.match, os.listdir(dirname)) if i is not None}
    if only:
        to_load &= only
    if exclude:
        to_load -= exclude
    return sorted(to_load)


def load_module(name: str, ignored_errors: Sequence[str]) -> Any:
    try:
        return import_module(name)
    except ImportError as e:
        if str(e) not in ignored_errors:
            traceback.print_exc()


def load_modules(
    to_load: Sequence[str],
    load: Callable[[str], Any],
    attr: str,
    modules_dict: Dict[str, Any],
    excluded_aliases: Set[str],
    loading_message: Optional[str] = None,
) -> None:
    if loading_message:
        print(loading_message)

    for name in to_load:
        module = load(name)

        if module is None or not hasattr(module, attr):
            continue

        cls = getattr(module, attr)
        if hasattr(cls, 'initialize') and not cls.initialize():
            continue

        if hasattr(module, 'aliases'):
            for alias in module.aliases():
                if alias not in excluded_aliases:
                    modules_dict[alias] = module
        else:
            modules_dict[name] = module

    if loading_message:
        print()
