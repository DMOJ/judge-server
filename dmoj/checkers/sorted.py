from re import split as resplit
from typing import Any, List

from dmoj.error import InternalError
from dmoj.utils.unicode import utf8bytes


def check(process_output: bytes, judge_output: bytes, split_on: str = 'lines', **kwargs) -> bool:
    split_pattern = {'lines': b'[\r\n]', 'whitespace': br'[\s]'}.get(split_on)

    if not split_pattern:
        raise InternalError('invalid `split_on` mode')

    process_lines: List[Any]
    judge_lines: List[Any]

    process_lines = list(filter(None, resplit(split_pattern, utf8bytes(process_output))))
    judge_lines = list(filter(None, resplit(split_pattern, utf8bytes(judge_output))))

    if len(process_lines) != len(judge_lines):
        return False

    if split_on == 'lines':
        process_lines = list(map(bytes.split, process_lines))
        judge_lines = list(map(bytes.split, judge_lines))

    process_lines.sort()
    judge_lines.sort()

    for process_line, judge_line in zip(process_lines, judge_lines):
        if process_line != judge_line:
            return False

    return True
