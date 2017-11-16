def check(process_output, judge_output, **kwargs):
    from six.moves import zip
    process_lines = list(filter(None, process_output.split(b'\n')))
    judge_lines = list(filter(None, judge_output.split(b'\n')))
    if len(process_lines) != len(judge_lines):
        return False
    for process_line, judge_line in zip(process_lines, judge_lines):
        if process_line.split() != judge_line.split():
            return False
    return True

try:
    from ._checker import standard
except ImportError as e:
    pass
else:
    def check(process_output, judge_output, _checker=standard, **kwargs):
        return _checker(judge_output, process_output)
    del standard
