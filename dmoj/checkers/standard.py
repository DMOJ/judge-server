from typing import Callable

from ._checker import standard
from ..utils.unicode import utf8bytes


def check(
    process_output: bytes, judge_output: bytes, _checker: Callable[[bytes, bytes], bool] = standard, **kwargs
) -> bool:
    return _checker(utf8bytes(judge_output), utf8bytes(process_output))


del standard
