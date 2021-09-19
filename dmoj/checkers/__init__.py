from typing import Callable, Union

from dmoj.checkers import (
    bridged,
    easy,
    floats,
    floatsabs,
    floatsrel,
    identical,
    linecount,
    linematches,
    rstripped,
    sorted,
    standard,
    unordered,
)
from dmoj.result import CheckerResult

CheckerOutput = Union[bool, CheckerResult]

CheckerCallable = Callable


class Checker:
    check: CheckerCallable
