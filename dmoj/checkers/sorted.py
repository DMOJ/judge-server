from re import split as resplit

import six
from six.moves import map, zip, filter

from dmoj.utils.unicode import utf8bytes


def check(process_output, judge_output, **kwargs):
    process_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(process_output))))
    judge_lines = list(filter(None, resplit(b'[\r\n]', utf8bytes(judge_output))))

    if len(process_lines) != len(judge_lines):
        return False

    process_lines = list(map(six.binary_type.split, process_lines))
    judge_lines = list(map(six.binary_type.split, judge_lines))
    process_lines.sort()
    judge_lines.sort()

    for process_line, judge_line in zip(process_lines, judge_lines):
        if process_line != judge_line:
            return False

    return True
