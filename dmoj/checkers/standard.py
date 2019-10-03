from typing import Optional

from ._checker import standard
from ..utils.unicode import utf8bytes


def check(process_output: bytes, judge_output: bytes, _checker: callable = standard,
          utf8bytes: Callable[..., bytes] = utf8bytes, **kwargs) -> bool:
    return _checker(utf8bytes(judge_output), utf8bytes(process_output))


del standard
