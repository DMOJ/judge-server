from re import split as resplit
from typing import List, Union

from dmoj.error import InternalError
from dmoj.result import CheckerResult
from dmoj.utils.unicode import utf8bytes


def check(
    process_output: bytes,
    judge_output: bytes,
    point_value: float = 1,
    point_distribution: List[int] = [1],
    filler_lines_required: bool = True,
    **kwargs
) -> Union[CheckerResult, bool]:
    judge_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(judge_output))))

    if len(judge_lines) != len(point_distribution):
        raise InternalError('point distribution length must equal to judge output length')

    if sum(point_distribution) == 0:
        raise InternalError('sum of point distribution must be positive')

    process_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(process_output))))

    if filler_lines_required and len(process_lines) != len(judge_lines):
        return False

    points = 0
    for process_line, judge_line, line_points in zip(process_lines, judge_lines, point_distribution):
        if process_line == judge_line:
            points += line_points

    return CheckerResult(points > 0, point_value * (points / sum(point_distribution)))
