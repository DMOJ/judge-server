from ._checker import standard
from ..utils.unicode import utf8bytes


def check(process_output, judge_output, _checker=standard, utf8bytes=utf8bytes, **kwargs):
    return _checker(utf8bytes(judge_output), utf8bytes(process_output))


del standard
