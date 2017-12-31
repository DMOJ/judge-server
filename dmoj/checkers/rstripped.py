from re import split as resplit

from six.moves import zip, filter

from dmoj.utils.unicode import utf8bytes


def check(process_output, judge_output, **kwargs):
    process_lines = resplit(b'[\r\n]', utf8bytes(process_output))
    judge_lines = resplit(b'[\r\n]', utf8bytes(judge_output))

    if 'filter_new_line' in kwargs:
        process_lines = list(filter(None, process_lines))
        judge_lines = list(filter(None, judge_lines))

    if len(process_lines) != len(judge_lines):
        return False

    for process_line, judge_line in zip(process_lines, judge_lines):
        if process_line.rstrip() != judge_line.rstrip():
            return False

    return True
